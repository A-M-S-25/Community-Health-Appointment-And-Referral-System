from flask import Blueprint, jsonify, render_template, request
from werkzeug.security import generate_password_hash

from app.models import HealthcareWorker, db
from app.services.auth_service import get_current_worker
from app.services.validation_service import ValidationError, validate_name
from app.utils.decorators import require_roles

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
def profile_page():
    worker = get_current_worker()
    if worker is None:
        return jsonify({'error': 'Authentication required. Please log in first.'}), 401
    return render_template('profile.html', worker=worker)


@profile_bp.route('/api/v1/profile', methods=['PATCH'])
@require_roles('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')
def update_profile():
    payload = request.get_json(silent=True) or {}
    if set(payload) - {'username', 'password'}:
        return jsonify({'error': 'Only username and password can be edited in your profile.'}), 400

    if 'username' in payload:
        try:
            username = validate_name(payload['username'], 'Username')
        except ValidationError as exc:
            return jsonify({'error': str(exc)}), 400
        existing = HealthcareWorker.query.filter(
            HealthcareWorker.username == username,
            HealthcareWorker.worker_id != request.worker.worker_id,
        ).first()
        if existing:
            return jsonify({'error': 'Username already exists.'}), 409
        request.worker.username = username

    if 'password' in payload:
        password = payload['password']
        if not isinstance(password, str) or len(password.strip()) < 6:
            return jsonify({'error': 'Password must contain at least 6 characters.'}), 400
        request.worker.password_hash = generate_password_hash(password.strip())

    db.session.commit()
    from flask import session
    session['worker_username'] = request.worker.username
    return jsonify({'message': 'Profile updated.', 'username': request.worker.username})
