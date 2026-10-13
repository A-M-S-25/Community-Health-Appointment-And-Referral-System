from flask import Blueprint, jsonify, render_template

from app.models import Appointment, Facility, Patient, Referral
from app.services.auth_service import get_current_worker
from app.services.audit_service import record_audit
from app.services.validation_service import REFERRAL_DESTINATION_TIERS

details_bp = Blueprint('details', __name__)


@details_bp.route('/patients/<int:patient_id>')
def patient_detail_page(patient_id):
    worker = get_current_worker()
    if worker is None:
        return jsonify({'error': 'Authentication required. Please log in first.'}), 401

    patient = Patient.query.get_or_404(patient_id)
    facility = Facility.query.get(worker.facility_id)
    if worker.role == 'L1':
        permitted = patient.community_unit_id in (None, worker.community_unit_id)
    elif worker.role == 'Admin':
        permitted = True
    else:
        permitted = facility is not None and facility.tier_level >= 2
    if not permitted:
        return jsonify({'error': 'You are not permitted to view this patient.'}), 403
    record_audit('view', 'patient', patient_id, worker_id=worker.worker_id)

    allowed_tiers = REFERRAL_DESTINATION_TIERS.get(worker.role, set())
    can_manage_patient = (
        worker.role != 'L1'
        or patient.community_unit_id == worker.community_unit_id
    )
    destinations = (
        Facility.query.filter(
            Facility.is_active.is_(True),
            Facility.tier_level.in_(allowed_tiers),
        ).order_by(Facility.tier_level.asc(), Facility.name.asc()).all()
        if allowed_tiers else []
    )
    return render_template(
        'patient_detail.html',
        patient=patient,
        facility=facility,
        referral_destinations=destinations,
        can_manage_patient=can_manage_patient,
    )


@details_bp.route('/referrals/<int:referral_id>')
def referral_detail_page(referral_id):
    worker = get_current_worker()
    if worker is None:
        return jsonify({'error': 'Authentication required. Please log in first.'}), 401

    referral = Referral.query.get_or_404(referral_id)
    if worker.role == 'L1':
        permitted = worker.community_unit_id == referral.origin_community_unit_id
    elif worker.role == 'Admin':
        permitted = True
    else:
        permitted = worker.facility_id == referral.destination_facility_id
    if not permitted:
        return jsonify({'error': 'You are not permitted to view this referral.'}), 403
    record_audit('view', 'referral', referral_id, worker_id=worker.worker_id)

    return render_template('referral_detail.html', referral=referral)


@details_bp.route('/appointments/<int:appointment_id>')
def appointment_detail_page(appointment_id):
    worker = get_current_worker()
    if worker is None:
        return jsonify({'error': 'Authentication required. Please log in first.'}), 401

    appointment = Appointment.query.get_or_404(appointment_id)
    if worker.role != 'Admin' and appointment.facility_id != worker.facility_id:
        return jsonify({'error': 'You are not permitted to view this appointment.'}), 403
    record_audit('view', 'appointment', appointment_id, worker_id=worker.worker_id)

    return render_template('appointment_detail.html', appointment=appointment)
