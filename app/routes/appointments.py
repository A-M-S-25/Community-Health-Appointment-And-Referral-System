from flask import Blueprint, jsonify, request
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from app.models import Appointment, AppointmentSlot, Facility, Patient, Referral, ReferralAppointment, db
from app.services.sms_service import send_sms
from app.services.audit_service import record_audit
from app.services.validation_service import ValidationError, parse_iso_datetime, validate_appointment_payload
from app.utils.decorators import require_roles

appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('/api/v1/patients/<int:patient_id>/appointments', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def book_patient_appointment(patient_id):
    patient = db.session.get(Patient, patient_id)
    slot_id = (request.get_json(silent=True) or {}).get('slot_id')
    try:
        slot_id = int(slot_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'slot_id must be an integer.'}), 400
    slot = (
        db.session.query(AppointmentSlot)
        .filter_by(slot_id=slot_id)
        .with_for_update()
        .first()
    )
    if patient is None or slot is None:
        return jsonify({'error': 'Patient or appointment slot was not found.'}), 404
    if request.worker.role != 'Admin' and slot.facility_id != request.worker.facility_id:
        return jsonify({'error': 'You can only book appointments at your assigned facility.'}), 403
    facility = db.session.get(Facility, slot.facility_id)
    if facility is None or facility.tier_level < 2:
        return jsonify({'error': 'Direct clinical appointments are available only at tier 2-6 facilities.'}), 403
    if slot.status != 'Available':
        return jsonify({'error': 'Slot is no longer available.'}), 409

    appointment = Appointment(
        patient_id=patient.patient_id,
        facility_id=slot.facility_id,
        appointment_datetime=slot.appointment_datetime,
        is_locked=True,
    )
    slot.status = 'Booked'
    db.session.add(appointment)
    db.session.commit()
    record_audit(
        'book',
        'appointment',
        appointment.appointment_id,
        {'patient_id': patient.patient_id, 'referral_id': None},
        request.worker.worker_id,
    )
    sms_status = send_sms(
        patient.phone_number,
        f'Your appointment has been booked for {slot.appointment_datetime} at {slot.facility.name}.',
        'appointment_confirmation',
    )
    return jsonify({
        'message': 'Patient appointment booked successfully.',
        'appointment_id': appointment.appointment_id,
        'patient_id': patient.patient_id,
        'facility_id': slot.facility_id,
        'appointment_datetime': slot.appointment_datetime.isoformat(),
        'sms': sms_status,
    }), 201


@appointments_bp.route('/api/v1/appointments/confirm', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def confirm_appointment():
    payload = request.get_json(silent=True) or {}
    referral_id = payload.get('referral_id')
    appointment_id = payload.get('appointment_id')

    if referral_id is None or appointment_id is None:
        return jsonify({'error': 'referral_id and appointment_id are required.'}), 400

    try:
        referral_id = int(referral_id)
        appointment_id = int(appointment_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'referral_id and appointment_id must be integers.'}), 400

    referral = db.session.get(Referral, referral_id)
    appointment = (
        db.session.query(Appointment)
        .filter_by(appointment_id=appointment_id)
        .with_for_update()
        .first()
    )

    if referral is None or appointment is None:
        return jsonify({'error': 'Referral or appointment was not found.'}), 404

    if request.worker.role != 'Admin' and (
        referral.destination_facility_id != request.worker.facility_id
        or appointment.facility_id != request.worker.facility_id
    ):
        return jsonify({'error': 'You can only book appointments at your assigned facility.'}), 403

    if appointment.referral_id != referral.referral_id:
        return jsonify({'error': 'Appointment does not belong to the supplied referral.'}), 400

    if referral.status in ('Booked', 'Completed', 'Cancelled'):
        return jsonify({'error': f'Referral is already {referral.status.lower()}.'}), 409

    if appointment.is_locked:
        return jsonify({'error': 'Appointment slot is already booked.', 'status': referral.status}), 409

    result = db.session.execute(
        update(Appointment)
        .where(
            Appointment.appointment_id == appointment_id,
            Appointment.is_locked.is_(False)
        )
        .values(is_locked=True)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.session.rollback()
        return jsonify({'error': 'Appointment slot is already booked.', 'status': referral.status}), 409

    referral.status = 'Booked'
    db.session.commit()
    record_audit(
        'book',
        'appointment',
        appointment.appointment_id,
        {'referral_id': referral.referral_id},
        request.worker.worker_id,
    )

    sms_message = (
        f'Your appointment has been confirmed for {appointment.appointment_datetime} '
        f'at {referral.destination_facility.name}.'
    )
    sms_status = send_sms(referral.patient.phone_number, sms_message)

    return jsonify({
        'message': 'Appointment confirmed successfully.',
        'referral_id': referral.referral_id,
        'appointment_id': appointment.appointment_id,
        'status': referral.status,
        'sms': sms_status
    })


@appointments_bp.route('/api/v1/appointments', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def create_appointment_slot():
    payload = request.get_json(silent=True) or {}
    try:
        validated = validate_appointment_payload(payload)
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400

    referral = db.session.get(Referral, validated['referral_id'])
    if not referral:
        return jsonify({'error': 'referral_id does not exist.'}), 400

    facility = db.session.get(Facility, validated['facility_id'])
    if not facility:
        return jsonify({'error': 'facility_id does not exist.'}), 400

    if facility.facility_id != referral.destination_facility_id:
        return jsonify({'error': 'Appointment facility must match the referral destination facility.'}), 400

    if request.worker.role != 'Admin' and validated['facility_id'] != request.worker.facility_id:
        return jsonify({'error': 'You can only create slots for your assigned facility.'}), 403

    appointment = Appointment(
        referral_id=referral.referral_id,
        facility_id=validated['facility_id'],
        appointment_datetime=validated['appointment_datetime'],
        is_locked=False
    )
    db.session.add(appointment)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'error': 'An appointment slot already exists at that facility and time.'
        }), 409

    return jsonify({
        'message': 'Appointment slot created.',
        'appointment_id': appointment.appointment_id,
        'referral_id': appointment.referral_id,
        'facility_id': appointment.facility_id,
        'appointment_datetime': appointment.appointment_datetime.isoformat()
    }), 201


@appointments_bp.route('/api/v1/appointment-slots', methods=['GET'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def list_appointment_slots():
    facility_id = request.args.get('facility_id', type=int)
    query = AppointmentSlot.query.filter_by(status='Available')
    if facility_id:
        query = query.filter_by(facility_id=facility_id)
    slots = query.order_by(AppointmentSlot.appointment_datetime.asc()).all()
    return jsonify([
        {
            'slot_id': slot.slot_id,
            'facility_id': slot.facility_id,
            'appointment_datetime': slot.appointment_datetime.isoformat(),
            'status': slot.status,
        }
        for slot in slots
    ])


@appointments_bp.route('/api/v1/appointments', methods=['GET'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def list_appointments():
    query = ReferralAppointment.query.join(Referral).join(AppointmentSlot)
    if request.worker.role != 'Admin':
        query = query.filter(AppointmentSlot.facility_id == request.worker.facility_id)
    status = request.args.get('status')
    if status:
        query = query.filter(ReferralAppointment.status == status)
    bookings = query.order_by(AppointmentSlot.appointment_datetime.asc()).all()
    return jsonify([
        {
            'booking_id': booking.booking_id,
            'referral_id': booking.referral_id,
            'patient_id': booking.referral.patient_id,
            'patient_name': booking.referral.patient.demographics.get('name', 'Unknown'),
            'facility_id': booking.slot.facility_id,
            'appointment_datetime': booking.slot.appointment_datetime.isoformat(),
            'status': booking.status,
            'referral_status': booking.referral.status,
        }
        for booking in bookings
    ])


@appointments_bp.route('/api/v1/appointment-slots', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def create_reusable_slot():
    payload = request.get_json(silent=True) or {}
    try:
        facility_id = int(payload.get('facility_id'))
        appointment_datetime = parse_iso_datetime(payload.get('appointment_datetime'))
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'facility_id must be an integer.'}), 400

    if request.worker.role != 'Admin' and facility_id != request.worker.facility_id:
        return jsonify({'error': 'You can only create slots for your assigned facility.'}), 403

    slot = AppointmentSlot(
        facility_id=facility_id,
        appointment_datetime=appointment_datetime,
        created_by=request.worker.worker_id,
    )
    db.session.add(slot)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'A slot already exists at that facility and time.'}), 409

    return jsonify({
        'slot_id': slot.slot_id,
        'facility_id': slot.facility_id,
        'appointment_datetime': slot.appointment_datetime.isoformat(),
        'status': slot.status,
    }), 201


@appointments_bp.route('/api/v1/appointment-slots/<int:slot_id>/book', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def book_reusable_slot(slot_id):
    from app.services.referral_service import transition_referral

    payload = request.get_json(silent=True) or {}
    referral_id = payload.get('referral_id')
    if referral_id is None:
        return jsonify({'error': 'referral_id is required.'}), 400
    try:
        referral_id = int(referral_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'referral_id must be an integer.'}), 400

    slot = (
        db.session.query(AppointmentSlot)
        .filter_by(slot_id=slot_id)
        .with_for_update()
        .first()
    )
    referral = db.session.get(Referral, referral_id)
    if slot is None or referral is None:
        return jsonify({'error': 'Slot or referral was not found.'}), 404
    if request.worker.role != 'Admin' and slot.facility_id != request.worker.facility_id:
        return jsonify({'error': 'You can only book slots at your assigned facility.'}), 403
    if slot.facility_id != referral.destination_facility_id:
        return jsonify({'error': 'Slot facility must match the referral destination.'}), 400
    if slot.status != 'Available':
        return jsonify({'error': 'Slot is no longer available.'}), 409
    if referral.status != 'Accepted':
        return jsonify({'error': f'Referral is {referral.status.lower()} and cannot be booked.'}), 409

    slot.status = 'Booked'
    booking = ReferralAppointment(
        referral_id=referral.referral_id,
        slot_id=slot.slot_id,
        booked_by=request.worker.worker_id,
    )
    db.session.add(booking)
    transition_referral(referral, 'Booked')
    db.session.commit()
    record_audit('book', 'appointment_slot', slot_id, {'referral_id': referral_id}, request.worker.worker_id)
    send_sms(
        referral.patient.phone_number,
        f'Your appointment has been confirmed for {slot.appointment_datetime} at {slot.facility.name}.',
        'booking_confirmation',
    )
    return jsonify({
        'booking_id': booking.booking_id,
        'slot_id': slot.slot_id,
        'referral_id': referral.referral_id,
        'status': referral.status,
    }), 201


@appointments_bp.route('/api/v1/referral-appointments/<int:booking_id>/status', methods=['PATCH'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def update_booking_status(booking_id):
    from app.services.referral_service import transition_referral

    booking = (
        db.session.query(ReferralAppointment)
        .join(AppointmentSlot)
        .filter(ReferralAppointment.booking_id == booking_id)
        .with_for_update()
        .first()
    )
    if booking is None:
        return jsonify({'error': 'Appointment booking was not found.'}), 404
    if request.worker.role != 'Admin' and booking.slot.facility_id != request.worker.facility_id:
        return jsonify({'error': 'You can only update appointments at your assigned facility.'}), 403

    requested_status = (request.get_json(silent=True) or {}).get('status')
    if requested_status not in {'Completed', 'Cancelled'}:
        return jsonify({'error': 'status must be Completed or Cancelled.'}), 400
    if booking.status != 'Booked' or booking.referral.status != 'Booked':
        return jsonify({'error': f'Appointment is already {booking.status.lower()}.'}), 409

    new_referral_status = requested_status
    try:
        transition_referral(booking.referral, new_referral_status)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409

    booking.status = requested_status
    if requested_status == 'Cancelled':
        booking.slot.status = 'Available'
    db.session.commit()
    record_audit(
        'status_change',
        'appointment',
        booking_id,
        {'status': requested_status, 'referral_id': booking.referral_id},
        request.worker.worker_id,
    )
    return jsonify({
        'message': f'Appointment marked {requested_status.lower()}.',
        'booking_id': booking_id,
        'status': requested_status,
    })


@appointments_bp.route('/api/v1/referrals/<int:referral_id>/decision', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def decide_referral(referral_id):
    from app.services.referral_service import transition_referral

    referral = db.session.get(Referral, referral_id)
    if referral is None:
        return jsonify({'error': 'Referral was not found.'}), 404
    if request.worker.role != 'Admin' and referral.destination_facility_id != request.worker.facility_id:
        return jsonify({'error': 'You can only decide referrals routed to your facility.'}), 403
    decision = (request.get_json(silent=True) or {}).get('decision')
    new_status = {'accept': 'Accepted', 'reject': 'Rejected'}.get(decision)
    if new_status is None:
        return jsonify({'error': 'decision must be accept or reject.'}), 400
    if new_status == 'Accepted' and not AppointmentSlot.query.filter_by(
        facility_id=referral.destination_facility_id,
        status='Available',
    ).first():
        return jsonify({'error': 'This referral cannot be accepted because no appointment slots are available.'}), 409
    try:
        transition_referral(referral, new_status)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    db.session.commit()
    record_audit('status_change', 'referral', referral_id, {'status': new_status}, request.worker.worker_id)
    return jsonify({'message': f'Referral {new_status.lower()}.', 'referral_id': referral_id, 'status': new_status})


@appointments_bp.route('/api/v1/referrals/<int:referral_id>/status', methods=['PATCH'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def update_referral_status(referral_id):
    from app.services.referral_service import transition_referral

    referral = db.session.get(Referral, referral_id)
    if referral is None:
        return jsonify({'error': 'Referral was not found.'}), 404
    if request.worker.role != 'Admin' and request.worker.facility_id not in (
        referral.origin_facility_id,
        referral.destination_facility_id,
    ):
        return jsonify({'error': 'You are not assigned to this referral.'}), 403

    new_status = (request.get_json(silent=True) or {}).get('status')
    try:
        transition_referral(referral, new_status)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    db.session.commit()
    record_audit('status_change', 'referral', referral_id, {'status': new_status}, request.worker.worker_id)
    return jsonify({'referral_id': referral_id, 'status': referral.status})
