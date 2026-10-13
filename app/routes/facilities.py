from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.models import AppointmentSlot, Facility, Patient, PatientAdmission, db
from app.utils.decorators import require_roles

facilities_bp = Blueprint('facilities', __name__)


@facilities_bp.route('/api/v1/facilities/availability', methods=['GET'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def get_availability():
    tier_level = request.args.get('tier_level', type=int)
    location = request.args.get('location', '').strip()
    maximum_tier = 3 if request.worker.role == 'L1' else 6

    if tier_level is not None and (tier_level < 2 or tier_level > maximum_tier):
        return jsonify({'error': f'tier_level must be between 2 and {maximum_tier} for this role.'}), 400

    query = Facility.query.filter(
        Facility.is_active.is_(True),
        Facility.tier_level >= 2,
        Facility.tier_level <= maximum_tier,
    )
    if tier_level is not None:
        query = query.filter(Facility.tier_level >= tier_level)
    if location:
        query = query.filter(Facility.contact_info.like(f'%{location}%'))

    results = []
    for facility in query.all():
        available_slots = AppointmentSlot.query.filter_by(
            facility_id=facility.facility_id,
            status='Available',
        ).count()
        if request.args.get('available_only') == 'true' and available_slots == 0:
            continue
        results.append({
            'facility_id': facility.facility_id,
            'name': facility.name,
            'tier_level': facility.tier_level,
            'location': facility.contact_info,
            'available_slots': available_slots
            ,'capacity': facility.capacity
            ,'occupied_capacity': facility.occupied_capacity
            ,'available_capacity': facility.available_capacity
        })

    return jsonify(results)


@facilities_bp.route('/api/v1/facilities/<int:facility_id>/admissions', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def admit_patient(facility_id):
    facility = (
        db.session.query(Facility)
        .filter_by(facility_id=facility_id)
        .with_for_update()
        .first()
    )
    patient_id = (request.get_json(silent=True) or {}).get('patient_id')
    patient = (
        db.session.query(Patient)
        .filter_by(patient_id=patient_id)
        .with_for_update()
        .first()
        if patient_id is not None else None
    )
    if facility is None or patient is None:
        return jsonify({'error': 'Facility or patient was not found.'}), 404
    if not facility.is_active:
        return jsonify({'error': 'The facility is inactive.'}), 400
    if request.worker.role != 'Admin' and request.worker.facility_id != facility_id:
        return jsonify({'error': 'You can only admit patients at your assigned facility.'}), 403
    if PatientAdmission.query.filter_by(patient_id=patient_id, discharged_at=None).first():
        return jsonify({'error': 'Patient is already admitted.'}), 409
    if facility.available_capacity < 1:
        return jsonify({'error': 'Facility has no available capacity.'}), 409

    admission = PatientAdmission(patient_id=patient_id, facility_id=facility_id)
    db.session.add(admission)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Patient could not be admitted.'}), 409
    return jsonify({
        'admission_id': admission.admission_id,
        'patient_id': patient_id,
        'facility_id': facility_id,
        'occupied_capacity': facility.occupied_capacity,
        'available_capacity': facility.available_capacity,
    }), 201


@facilities_bp.route('/api/v1/admissions/<int:admission_id>/discharge', methods=['POST'])
@require_roles('L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def discharge_patient(admission_id):
    admission = db.session.get(PatientAdmission, admission_id)
    if admission is None:
        return jsonify({'error': 'Admission was not found.'}), 404
    if request.worker.role != 'Admin' and request.worker.facility_id != admission.facility_id:
        return jsonify({'error': 'You can only discharge patients at your assigned facility.'}), 403
    if admission.discharged_at is not None:
        return jsonify({'error': 'Patient has already been discharged.'}), 409
    admission.discharged_at = datetime.utcnow()
    db.session.commit()
    facility = db.session.get(Facility, admission.facility_id)
    return jsonify({
        'admission_id': admission.admission_id,
        'discharged_at': admission.discharged_at.isoformat(),
        'occupied_capacity': facility.occupied_capacity,
        'available_capacity': facility.available_capacity,
    })
