from flask import Blueprint, jsonify, render_template, request

from app.models import AppointmentSlot, CommunityHealthUnit, Patient, Referral, Facility, db
from app.services.sms_service import send_sms
from app.services.audit_service import record_audit
from app.services.validation_service import (
    ValidationError,
    validate_patient_payload,
    validate_referral_route,
    validate_referral_payload,
    normalize_phone,
)
from app.utils.decorators import require_roles

patients_bp = Blueprint('patients', __name__)


@patients_bp.route('/api/v1/referrals', methods=['GET'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def list_referrals():
    query = Referral.query
    if request.worker.role == 'L1':
        query = query.filter(Referral.origin_community_unit_id == request.worker.community_unit_id)
    elif request.worker.role != 'Admin':
        query = query.filter(Referral.destination_facility_id == request.worker.facility_id)
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    referrals = query.order_by(Referral.created_at.desc()).limit(100).all()
    return jsonify([
        {
            'referral_id': referral.referral_id,
            'patient_id': referral.patient_id,
            'patient_name': referral.patient.demographics.get('name', 'Unknown'),
            'status': referral.status,
            'origin_facility': referral.origin_facility.name if referral.origin_facility else referral.origin_community_unit.name,
            'destination_facility': referral.destination_facility.name,
            'destination_facility_id': referral.destination_facility_id,
            'created_at': referral.created_at.isoformat(),
        }
        for referral in referrals
    ])


@patients_bp.route('/api/v1/patients/onboard', methods=['POST'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6')
def onboard_patient():
    payload = request.get_json(silent=True) or {}

    try:
        validated = validate_patient_payload(payload)
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400

    phone_number = validated['phone_number']
    demographics = validated['demographics']
    patient = Patient.query.filter_by(phone_number=phone_number).first()
    if patient is None:
        patient = Patient(
            phone_number=phone_number,
            demographics={},
            community_unit_id=(
                request.worker.community_unit_id
                if request.worker.role == 'L1' else None
            ),
        )
        db.session.add(patient)
        db.session.flush()
    elif request.worker.role == 'L1':
        if patient.community_unit_id not in (None, request.worker.community_unit_id):
            return jsonify({'error': 'Patient belongs to another community health unit.'}), 403
        if patient.community_unit_id is None:
            patient.community_unit_id = request.worker.community_unit_id

    patient.demographics = {**patient.demographics, **demographics}
    db.session.commit()
    record_audit(
        'create',
        'patient',
        patient.patient_id,
        {
            'registration_facility_id': request.worker.facility_id,
            'community_unit_id': patient.community_unit_id,
        },
        request.worker.worker_id,
    )

    sms_status = send_sms(
        phone_number,
        'Your patient record has been created in the community health system.',
        'patient_registration',
    )

    return jsonify({
        'message': 'Patient registered successfully. No referral was created.',
        'patient_id': patient.patient_id,
        'sms': sms_status
    }), 201


@patients_bp.route('/api/v1/patients/<int:patient_id>', methods=['GET'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def patient_history(patient_id):
    patient = db.session.get(Patient, patient_id)
    if patient is None:
        return jsonify({'error': 'Patient was not found.'}), 404

    if request.worker.role == 'L1':
        if patient.community_unit_id not in (None, request.worker.community_unit_id):
            return jsonify({'error': 'You are not permitted to view this patient.'}), 403
    elif request.worker.role != 'Admin':
        facility = db.session.get(Facility, request.worker.facility_id)
        if facility is None or facility.tier_level < 2:
            return jsonify({'error': 'Only tier 2-6 clinicians may access cross-facility patient history.'}), 403

    record_audit('view', 'patient', patient_id, worker_id=request.worker.worker_id)
    return jsonify({
        'patient_id': patient.patient_id,
        'phone_number': patient.phone_number,
        'demographics': patient.demographics,
        'community_unit_id': patient.community_unit_id,
        'community_unit': patient.community_unit.name if patient.community_unit else 'UNKNOWN',
        'triage_data': patient.triage_data,
        'referrals': [
            {
                'referral_id': referral.referral_id,
                'origin_facility': referral.origin_facility.name if referral.origin_facility else referral.origin_community_unit.name,
                'destination_facility': referral.destination_facility.name,
                'status': referral.status,
                'triage_notes': referral.triage_notes,
                'created_at': referral.created_at.isoformat(),
            }
            for referral in patient.referrals
        ],
        'appointments': [
            {
                'appointment_id': appointment.appointment_id,
                'facility_id': appointment.facility_id,
                'appointment_datetime': appointment.appointment_datetime.isoformat(),
                'is_locked': appointment.is_locked,
                'referral_id': appointment.referral_id,
            }
            for appointment in patient.appointments
        ],
    })


@patients_bp.route('/api/v1/patients/search', methods=['GET'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def search_patients():
    phone_number = normalize_phone(request.args.get('phone_number', ''))
    if not phone_number:
        return jsonify({'error': 'phone_number is required.'}), 400
    patient = Patient.query.filter_by(phone_number=phone_number).first()
    if patient is None:
        return jsonify({'error': 'Patient was not found.'}), 404
    return patient_history(patient.patient_id)


@patients_bp.route('/api/v1/patients', methods=['GET'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def list_patients():
    query = Patient.query.order_by(Patient.patient_id.desc())
    if request.worker.role == 'L1':
        query = query.filter(
            (Patient.community_unit_id == request.worker.community_unit_id)
            | (Patient.community_unit_id.is_(None))
        )
    patients = query.limit(100).all()
    return jsonify([
        {
            'patient_id': patient.patient_id,
            'name': patient.demographics.get('name', 'Unknown'),
            'phone_number': patient.phone_number,
            'community_unit': patient.community_unit.name if patient.community_unit else 'UNKNOWN',
        }
        for patient in patients
    ])


@patients_bp.route('/api/v1/patients/<int:patient_id>/triage', methods=['PATCH'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def update_patient_triage(patient_id):
    patient = db.session.get(Patient, patient_id)
    if patient is None:
        return jsonify({'error': 'Patient was not found.'}), 404
    if request.worker.role == 'L1' and patient.community_unit_id != request.worker.community_unit_id:
        return jsonify({'error': 'You can only update triage for patients in your community health unit.'}), 403
    payload = request.get_json(silent=True) or {}
    triage_data = payload.get('triage_data')
    if triage_data is None and 'triage_notes' in payload:
        triage_data = {'notes': str(payload['triage_notes']).strip()}
    if not isinstance(triage_data, dict):
        return jsonify({'error': 'triage_data must be a JSON object.'}), 400
    patient.triage_data = triage_data
    db.session.commit()
    record_audit('update', 'patient_triage', patient_id, triage_data, request.worker.worker_id)
    return jsonify({'message': 'Patient triage updated.', 'patient_id': patient_id, 'triage_data': patient.triage_data})


@patients_bp.route('/api/v1/patients/<int:patient_id>/referrals', methods=['POST'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def create_referral(patient_id):
    patient = db.session.get(Patient, patient_id)
    if patient is None:
        return jsonify({'error': 'Patient was not found.'}), 404
    if request.worker.role == 'L1' and patient.community_unit_id != request.worker.community_unit_id:
        return jsonify({'error': 'You can only refer patients in your community health unit.'}), 403

    try:
        validated = validate_referral_payload(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400

    origin = db.session.get(Facility, request.worker.facility_id) if request.worker.facility_id else None
    origin_community_unit = (
        db.session.get(CommunityHealthUnit, request.worker.community_unit_id)
        if request.worker.community_unit_id else None
    )
    destination = db.session.get(Facility, validated['destination_facility_id'])
    if (origin is None and origin_community_unit is None) or destination is None:
        return jsonify({'error': 'Origin or destination facility was not found.'}), 400
    if not destination.is_active:
        return jsonify({'error': 'The destination facility is inactive.'}), 400
    if not AppointmentSlot.query.filter_by(
        facility_id=destination.facility_id,
        status='Available',
    ).first():
        return jsonify({'error': 'The destination facility has no available appointment slots.'}), 409
    try:
        validate_referral_route(request.worker.role, destination.tier_level)
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400
    if origin is not None and destination.tier_level <= origin.tier_level:
        return jsonify({'error': 'Referrals from this facility must move to a higher tier.'}), 400

    referral = Referral(
        patient_id=patient.patient_id,
        origin_facility_id=origin.facility_id if origin else None,
        origin_community_unit_id=origin_community_unit.community_unit_id if origin_community_unit else None,
        destination_facility_id=destination.facility_id,
        triage_notes=validated['triage_notes'],
        status='Pending',
    )
    db.session.add(referral)
    db.session.commit()
    record_audit(
        'create',
        'referral',
        referral.referral_id,
        {'patient_id': patient.patient_id, 'upward_referral': True},
        request.worker.worker_id,
    )
    return jsonify({
        'message': 'Upward referral created successfully.',
        'referral_id': referral.referral_id,
        'patient_id': patient.patient_id,
        'status': referral.status,
    }), 201
