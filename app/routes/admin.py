import csv
import io
import json
from datetime import datetime

from flask import Blueprint, jsonify, make_response, render_template, request
from werkzeug.security import generate_password_hash

from app.models import (
    Appointment, AppointmentSlot, AuditLog, CommunityHealthUnit, Facility,
    HealthcareWorker, Patient, PatientAdmission, Referral, ReferralAppointment, db
)
from app.services.audit_service import record_audit
from app.services.validation_service import (
    ValidationError,
    validate_community_unit_payload,
    validate_facility_payload,
    validate_name,
    validate_worker_payload,
)
from app.utils.decorators import require_roles

admin_bp = Blueprint('admin', __name__)


def normalize_contact_info(contact_info):
    if isinstance(contact_info, dict):
        return contact_info
    if isinstance(contact_info, str):
        try:
            parsed = json.loads(contact_info)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


@admin_bp.route('/admin', methods=['GET'])
@require_roles('Admin')
def admin_dashboard_page():
    dashboard = build_dashboard_data()
    if 'error' in dashboard:
        return jsonify(dashboard), 400
    return render_template('dashboard.html', dashboard=dashboard)


@admin_bp.route('/admin/facilities', methods=['GET'])
@require_roles('Admin')
def admin_facilities_page():
    facilities = Facility.query.order_by(Facility.tier_level.asc(), Facility.name.asc()).all()
    contact_info_by_facility_id = {
        facility.facility_id: normalize_contact_info(facility.contact_info)
        for facility in facilities
    }
    return render_template(
        'admin_facilities.html',
        facilities=facilities,
        contact_info_by_facility_id=contact_info_by_facility_id,
    )


@admin_bp.route('/admin/facilities/<int:facility_id>/edit', methods=['GET'])
@require_roles('Admin')
def edit_facility_page(facility_id):
    facility = db.session.get(Facility, facility_id)
    if facility is None:
        return 'Facility not found.', 404
    contact_info = normalize_contact_info(facility.contact_info)
    return render_template('admin_facility_edit.html', facility=facility, contact_info=contact_info)


@admin_bp.route('/admin/workers', methods=['GET'])
@require_roles('Admin')
def admin_workers_page():
    workers = HealthcareWorker.query.order_by(HealthcareWorker.worker_id.asc()).all()
    active_admin_count = HealthcareWorker.query.filter_by(role='Admin', is_active=True).count()
    return render_template(
        'admin_workers.html',
        workers=workers,
        active_admin_count=active_admin_count,
    )


@admin_bp.route('/admin/workers/<int:worker_id>/edit', methods=['GET'])
@require_roles('Admin')
def edit_worker_page(worker_id):
    worker = db.session.get(HealthcareWorker, worker_id)
    if worker is None:
        return 'User not found.', 404
    facilities = Facility.query.filter_by(is_active=True).order_by(Facility.name.asc()).all()
    units = CommunityHealthUnit.query.filter_by(is_active=True).order_by(CommunityHealthUnit.name.asc()).all()
    return render_template(
        'admin_user_edit.html',
        worker=worker,
        facilities=facilities,
        units=units,
    )


@admin_bp.route('/admin/community-units', methods=['GET'])
@require_roles('Admin')
def admin_community_units_page():
    units = CommunityHealthUnit.query.order_by(CommunityHealthUnit.name.asc()).all()
    return render_template('admin_community_units.html', units=units)


@admin_bp.route('/admin/community-units/<int:community_unit_id>/edit', methods=['GET'])
@require_roles('Admin')
def edit_community_unit_page(community_unit_id):
    unit = db.session.get(CommunityHealthUnit, community_unit_id)
    if unit is None:
        return 'Community health unit not found.', 404
    return render_template('admin_community_unit_edit.html', unit=unit)


@admin_bp.route('/api/v1/admin/dashboard', methods=['GET'])
@require_roles('Admin')
def admin_dashboard_api():
    return jsonify(build_dashboard_data())


@admin_bp.route('/api/v1/admin/audit-logs', methods=['GET'])
@require_roles('Admin')
def list_audit_logs():
    from app.models import AuditLog
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return jsonify([
        {
            'audit_id': log.audit_id,
            'action': log.action,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'worker_id': log.worker_id,
            'created_at': log.created_at.isoformat(),
        }
        for log in logs
    ])


@admin_bp.route('/admin/reports.csv', methods=['GET'])
@require_roles('Admin')
def export_reports_csv():
    query = Referral.query
    status = request.args.get('status')
    destination_id = request.args.get('destination_facility_id', type=int)
    if status:
        query = query.filter_by(status=status)
    if destination_id:
        query = query.filter_by(destination_facility_id=destination_id)
    referrals = query.order_by(Referral.referral_id.asc()).all()
    record_audit(
        'export',
        'referrals',
        metadata={'format': 'csv', 'status': status, 'destination_facility_id': destination_id},
        worker_id=request.worker.worker_id,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Referral ID', 'Patient', 'Phone', 'Origin Facility',
        'Destination Facility', 'Status', 'Triage Notes', 'Appointments'
    ])
    for referral in referrals:
        writer.writerow([
            referral.referral_id,
            referral.patient.demographics.get('name', 'Unknown'),
            referral.patient.phone_number,
            referral.origin_facility.name if referral.origin_facility else referral.origin_community_unit.name,
            referral.destination_facility.name,
            referral.status,
            referral.triage_notes,
            len(referral.appointments),
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=charsystem-referrals.csv'
    return response


@admin_bp.route('/admin/reports.pdf', methods=['GET'])
@require_roles('Admin')
def export_reports_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return jsonify({'error': 'PDF export is unavailable. Install dependencies from requirements.txt.'}), 503

    query = Referral.query
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    referrals = query.order_by(Referral.referral_id.asc()).all()
    record_audit(
        'export',
        'referrals',
        metadata={'format': 'pdf', 'status': status},
        worker_id=request.worker.worker_id,
    )
    buffer = io.BytesIO()
    document = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    document.setTitle('Community Health Referral Report')
    document.setFont('Helvetica-Bold', 15)
    document.drawString(40, y, 'Community Health Referral Report')
    y -= 25
    document.setFont('Helvetica', 9)
    document.drawString(40, y, f'Total referrals: {len(referrals)}')
    y -= 25

    for referral in referrals:
        patient_name = referral.patient.demographics.get('name', 'Unknown')
        line = (
            f'#{referral.referral_id} | {patient_name} | {referral.status} | '
            f'{referral.destination_facility.name}'
        )
        document.drawString(40, y, line[:115])
        y -= 15
        if y < 50:
            document.showPage()
            y = height - 50
            document.setFont('Helvetica', 9)

    document.save()
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=charsystem-referrals.pdf'
    return response


@admin_bp.route('/api/v1/admin/facilities', methods=['POST'])
@require_roles('Admin')
def create_facility():
    payload = request.get_json(silent=True) or {}

    try:
        validated = validate_facility_payload(payload)
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400

    facility = Facility(**validated)
    db.session.add(facility)
    db.session.commit()

    return jsonify({
        'message': 'Facility onboarded successfully.',
        'facility_id': facility.facility_id,
        'name': facility.name,
        'tier_level': facility.tier_level
    }), 201


@admin_bp.route('/api/v1/admin/facilities', methods=['GET'])
@require_roles('Admin')
def list_facilities():
    facilities = Facility.query.order_by(Facility.tier_level.asc(), Facility.name.asc()).all()
    return jsonify([
        {
            'facility_id': item.facility_id,
            'name': item.name,
            'tier_level': item.tier_level,
            'contact_info': item.contact_info,
            'capacity': item.capacity,
            'occupied_capacity': item.occupied_capacity,
            'available_capacity': item.available_capacity,
            'is_active': item.is_active
        }
        for item in facilities
    ])


@admin_bp.route('/api/v1/admin/community-units', methods=['GET'])
@require_roles('Admin')
def list_community_units():
    units = CommunityHealthUnit.query.order_by(CommunityHealthUnit.name.asc()).all()
    return jsonify([
        {
            'community_unit_id': unit.community_unit_id,
            'name': unit.name,
            'location': unit.location,
            'is_active': unit.is_active,
            'chp_count': len(unit.workers),
        }
        for unit in units
    ])


@admin_bp.route('/api/v1/admin/community-units', methods=['POST'])
@require_roles('Admin')
def create_community_unit():
    try:
        validated = validate_community_unit_payload(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400
    unit = CommunityHealthUnit(**validated)
    db.session.add(unit)
    db.session.commit()
    return jsonify({
        'message': 'Community health unit onboarded successfully.',
        'community_unit_id': unit.community_unit_id,
        'name': unit.name,
        'location': unit.location,
    }), 201


@admin_bp.route('/api/v1/admin/community-units/<int:community_unit_id>', methods=['PATCH'])
@require_roles('Admin')
def update_community_unit(community_unit_id):
    unit = db.session.get(CommunityHealthUnit, community_unit_id)
    if unit is None:
        return jsonify({'error': 'Community health unit not found.'}), 404
    payload = request.get_json(silent=True) or {}
    if 'name' in payload:
        unit.name = str(payload['name']).strip()
    if 'location' in payload:
        unit.location = str(payload['location']).strip()
    if 'is_active' in payload:
        unit.is_active = bool(payload['is_active'])
    if len(unit.name) < 2 or len(unit.location) < 2:
        return jsonify({'error': 'Community health unit name and location must contain at least 2 characters.'}), 400
    db.session.commit()
    return jsonify({'message': 'Community health unit updated.', 'community_unit_id': community_unit_id})


@admin_bp.route('/api/v1/admin/community-units/<int:community_unit_id>', methods=['DELETE'])
@require_roles('Admin')
def delete_community_unit(community_unit_id):
    unit = db.session.get(CommunityHealthUnit, community_unit_id)
    if unit is None:
        return jsonify({'error': 'Community health unit not found.'}), 404
    if unit.workers or unit.origin_referrals:
        return jsonify({
            'error': 'Community health unit cannot be deleted while it has assigned users or referrals.'
        }), 409
    db.session.delete(unit)
    db.session.commit()
    return jsonify({'message': 'Community health unit deleted.'})


@admin_bp.route('/api/v1/admin/workers', methods=['GET'])
@require_roles('Admin')
def list_workers():
    workers = HealthcareWorker.query.order_by(HealthcareWorker.worker_id.asc()).all()
    return jsonify([
        {
            'worker_id': worker.worker_id,
            'username': worker.username,
            'role': worker.role,
            'facility_id': worker.facility_id,
            'community_unit_id': worker.community_unit_id,
            'is_active': worker.is_active,
            'last_login_at': worker.last_login_at.isoformat() if worker.last_login_at else None
        }
        for worker in workers
    ])


@admin_bp.route('/api/v1/admin/workers', methods=['POST'])
@require_roles('Admin')
def create_worker():
    payload = request.get_json(silent=True) or {}

    try:
        validated = validate_worker_payload(payload)
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400

    if HealthcareWorker.query.filter_by(username=validated['username']).first():
        return jsonify({'error': 'Username already exists.'}), 409

    if validated['facility_id'] is not None and not Facility.query.get(validated['facility_id']):
        return jsonify({'error': 'facility_id does not exist.'}), 400
    if validated['community_unit_id'] is not None and not CommunityHealthUnit.query.get(validated['community_unit_id']):
        return jsonify({'error': 'community_unit_id does not exist.'}), 400

    worker = HealthcareWorker(
        facility_id=validated['facility_id'],
        community_unit_id=validated['community_unit_id'],
        username=validated['username'],
        role=validated['role'],
        password_hash=generate_password_hash(validated['password'])
    )
    db.session.add(worker)
    db.session.commit()

    return jsonify({
        'message': 'Worker credential issued.',
        'worker_id': worker.worker_id,
        'facility_id': worker.facility_id,
        'community_unit_id': worker.community_unit_id,
        'role': worker.role,
        'username': worker.username
    }), 201


@admin_bp.route('/api/v1/admin/facilities/<int:facility_id>', methods=['PATCH'])
@require_roles('Admin')
def update_facility(facility_id):
    facility = db.session.get(Facility, facility_id)
    if facility is None:
        return jsonify({'error': 'Facility not found.'}), 404
    payload = request.get_json(silent=True) or {}
    if 'name' in payload:
        try:
            facility.name = validate_name(payload['name'], 'Facility name')
        except ValidationError as exc:
            return jsonify({'error': str(exc)}), 400
    if 'tier_level' in payload:
        try:
            tier = int(payload['tier_level'])
        except (TypeError, ValueError):
            return jsonify({'error': 'tier_level must be an integer.'}), 400
        if tier < 2 or tier > 6:
            return jsonify({'error': 'tier_level must be between 2 and 6.'}), 400
        facility.tier_level = tier
    if 'capacity' in payload:
        try:
            capacity = int(payload['capacity'])
        except (TypeError, ValueError):
            return jsonify({'error': 'capacity must be a positive integer.'}), 400
        if capacity < facility.occupied_capacity:
            return jsonify({'error': 'capacity cannot be below current occupancy.'}), 400
        if capacity < 1:
            return jsonify({'error': 'capacity must be a positive integer.'}), 400
        facility.capacity = capacity
    if 'contact_info' in payload:
        contact_info = payload['contact_info']
        if isinstance(contact_info, str):
            try:
                contact_info = json.loads(contact_info)
            except json.JSONDecodeError as exc:
                return jsonify({'error': 'contact_info must be valid JSON or an object.'}), 400
        if not isinstance(contact_info, dict):
            return jsonify({'error': 'contact_info must be a JSON object.'}), 400
        facility.contact_info = json.dumps(contact_info, separators=(',', ':'))
    if 'is_active' in payload:
        facility.is_active = bool(payload['is_active'])
    db.session.commit()
    record_audit('update', 'facility', facility_id, payload, request.worker.worker_id)
    return jsonify({'message': 'Facility updated.', 'facility_id': facility_id})


@admin_bp.route('/api/v1/admin/facilities/<int:facility_id>', methods=['DELETE'])
@require_roles('Admin')
def delete_facility(facility_id):
    facility = db.session.get(Facility, facility_id)
    if facility is None:
        return jsonify({'error': 'Facility not found.'}), 404
    if (
        facility.workers or facility.origin_referrals or facility.destination_referrals
        or facility.admissions
        or Appointment.query.filter_by(facility_id=facility_id).first()
        or AppointmentSlot.query.filter_by(facility_id=facility_id).first()
    ):
        return jsonify({
            'error': 'Facility cannot be deleted while it has users, referrals, appointments, slots, or admissions.'
        }), 409
    db.session.delete(facility)
    db.session.commit()
    return jsonify({'message': 'Facility deleted.'})


@admin_bp.route('/api/v1/admin/workers/<int:worker_id>', methods=['PATCH'])
@require_roles('Admin')
def update_worker(worker_id):
    worker = db.session.get(HealthcareWorker, worker_id)
    if worker is None:
        return jsonify({'error': 'Worker not found.'}), 404
    payload = request.get_json(silent=True) or {}
    if 'username' in payload:
        try:
            username = validate_name(payload['username'], 'Username')
        except ValidationError as exc:
            return jsonify({'error': str(exc)}), 400
        existing = HealthcareWorker.query.filter(
            HealthcareWorker.username == username,
            HealthcareWorker.worker_id != worker_id,
        ).first()
        if existing:
            return jsonify({'error': 'Username already exists.'}), 409
        worker.username = username
    requested_role = payload.get('role', worker.role)
    requested_active = bool(payload['is_active']) if 'is_active' in payload else worker.is_active
    removing_admin_access = (
        worker.role == 'Admin'
        and worker.is_active
        and (requested_role != 'Admin' or not requested_active)
    )
    if removing_admin_access:
        active_admin_count = HealthcareWorker.query.filter_by(
            role='Admin',
            is_active=True,
        ).count()
        if active_admin_count <= 1:
            return jsonify({
                'error': 'The last active administrator cannot be deactivated or changed. '
                         'Create or activate another administrator first.'
            }), 409
    if 'role' in payload:
        if payload['role'] not in {'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin'}:
            return jsonify({'error': 'Invalid role.'}), 400
        worker.role = payload['role']
        if worker.role == 'L1':
            if 'community_unit_id' not in payload:
                return jsonify({'error': 'L1 workers must be assigned to a community health unit.'}), 400
            worker.facility_id = None
        elif worker.role == 'Admin':
            worker.facility_id = None
            worker.community_unit_id = None
        elif worker.community_unit_id is not None:
            worker.community_unit_id = None
    if 'facility_id' in payload:
        if worker.role in {'L1', 'Admin'}:
            return jsonify({'error': 'Only L2-L6 workers can be assigned to a facility.'}), 400
        facility = db.session.get(Facility, payload['facility_id'])
        if facility is None:
            return jsonify({'error': 'Facility not found.'}), 400
        worker.facility_id = facility.facility_id
    if 'community_unit_id' in payload:
        if worker.role != 'L1':
            return jsonify({'error': 'Only L1 workers can be assigned to a community health unit.'}), 400
        unit = db.session.get(CommunityHealthUnit, payload['community_unit_id'])
        if unit is None:
            return jsonify({'error': 'Community health unit not found.'}), 400
        worker.community_unit_id = unit.community_unit_id
    if 'is_active' in payload:
        worker.is_active = bool(payload['is_active'])
    if worker.role == 'L1' and (worker.facility_id is not None or worker.community_unit_id is None):
        return jsonify({'error': 'L1 workers require a community health unit and no facility.'}), 400
    if worker.role in {'L2', 'L3', 'L4', 'L5', 'L6'} and (
        worker.facility_id is None or worker.community_unit_id is not None
    ):
        return jsonify({'error': 'L2-L6 workers require a facility and no community health unit.'}), 400
    if worker.role == 'Admin' and (worker.facility_id is not None or worker.community_unit_id is not None):
        return jsonify({'error': 'Admin workers must not have a facility or community health unit assignment.'}), 400
    db.session.commit()
    record_audit('update', 'worker', worker_id, payload, request.worker.worker_id)
    return jsonify({'message': 'Worker updated.', 'worker_id': worker_id})


@admin_bp.route('/api/v1/admin/workers/<int:worker_id>', methods=['DELETE'])
@require_roles('Admin')
def delete_worker(worker_id):
    worker = db.session.get(HealthcareWorker, worker_id)
    if worker is None:
        return jsonify({'error': 'User not found.'}), 404
    if worker.role == 'Admin' and worker.is_active:
        active_admin_count = HealthcareWorker.query.filter_by(role='Admin', is_active=True).count()
        if active_admin_count <= 1:
            return jsonify({
                'error': 'The last active administrator cannot be deleted. '
                         'Create or activate another administrator first.'
            }), 409
    if (
        AppointmentSlot.query.filter_by(created_by=worker_id).first()
        or ReferralAppointment.query.filter_by(booked_by=worker_id).first()
        or AuditLog.query.filter_by(worker_id=worker_id).first()
    ):
        return jsonify({
            'error': 'User cannot be deleted because audit, appointment, or referral records reference the account.'
        }), 409
    if worker_id == request.worker.worker_id:
        return jsonify({'error': 'You cannot delete your own account.'}), 400
    db.session.delete(worker)
    db.session.commit()
    return jsonify({'message': 'User deleted.'})


@admin_bp.route('/api/v1/admin/workers/<int:worker_id>/password', methods=['POST'])
@require_roles('Admin')
def reset_worker_password(worker_id):
    from app.services.validation_service import validate_worker_payload
    from werkzeug.security import generate_password_hash

    worker = db.session.get(HealthcareWorker, worker_id)
    if worker is None:
        return jsonify({'error': 'Worker not found.'}), 404
    password = (request.get_json(silent=True) or {}).get('password')
    try:
        validated = validate_worker_payload({
            'facility_id': worker.facility_id,
            'community_unit_id': worker.community_unit_id,
            'username': worker.username,
            'role': worker.role,
            'password': password,
        })
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400
    worker.password_hash = generate_password_hash(validated['password'])
    db.session.commit()
    record_audit('password_reset', 'worker', worker_id, worker_id=request.worker.worker_id)
    return jsonify({'message': 'Worker password reset.'})


def build_dashboard_data():
    facilities = Facility.query.count()
    workers = HealthcareWorker.query.count()
    query = Referral.query
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if status:
        query = query.filter_by(status=status)
    try:
        if start_date:
            query = query.filter(Referral.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Referral.created_at < datetime.fromisoformat(end_date))
    except ValueError:
        return {'error': 'Dates must use ISO format YYYY-MM-DD.'}

    referrals = query.count()
    patients = Patient.query.count()
    appointments = Appointment.query.count()
    open_referrals = query.filter(Referral.status.notin_(['Completed', 'Cancelled'])).count()
    completed_referrals = query.filter_by(status='Completed').count()
    cancelled_referrals = query.filter_by(status='Cancelled').count()

    recent_referrals = query.order_by(Referral.referral_id.desc()).limit(5).all()
    recent_items = []
    for referral in recent_referrals:
        recent_items.append({
            'referral_id': referral.referral_id,
            'patient': referral.patient.demographics.get('name', 'Unknown'),
            'status': referral.status,
            'destination': referral.destination_facility.name,
            'triage_notes': referral.triage_notes[:80]
        })

    status_labels = ['Draft', 'Pending', 'Booked', 'Completed', 'Cancelled']
    status_breakdown = [
        {'label': label, 'value': query.filter_by(status=label).count()}
        for label in status_labels
    ]

    tier_breakdown = [
        {'label': f'Tier {tier}', 'value': Facility.query.filter_by(tier_level=tier).count()}
        for tier in range(1, 7)
        if Facility.query.filter_by(tier_level=tier).count() > 0
    ]

    role_breakdown = [
        {'label': role, 'value': HealthcareWorker.query.filter_by(role=role).count()}
        for role in ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin']
        if HealthcareWorker.query.filter_by(role=role).count() > 0
    ]

    return {
        'summary': {
            'facilities': facilities,
            'workers': workers,
            'referrals': referrals,
            'patients': patients,
            'appointments': appointments,
            'open_referrals': open_referrals
        },
        'outcome_metrics': {
            'completion_rate': round(completed_referrals / referrals * 100, 1) if referrals else 0,
            'cancellation_rate': round(cancelled_referrals / referrals * 100, 1) if referrals else 0,
        },
        'recent_referrals': recent_items,
        'status_breakdown': status_breakdown,
        'tier_breakdown': tier_breakdown,
        'role_breakdown': role_breakdown
    }
