from datetime import datetime

from flask import request, session
from werkzeug.security import check_password_hash

from app.models import HealthcareWorker, db
from app.services.audit_service import record_audit
from app.services.security_service import (
    clear_failed_logins,
    login_is_throttled,
    record_failed_login,
)


def login_worker(username, password):
    if login_is_throttled(username):
        return None
    worker = HealthcareWorker.query.filter_by(username=username).first()
    if worker and worker.is_active and check_password_hash(worker.password_hash, password):
        clear_failed_logins(username)
        session['worker_id'] = worker.worker_id
        session['worker_role'] = worker.role
        session['worker_username'] = worker.username
        worker.last_login_at = datetime.utcnow()
        db.session.commit()
        record_audit('login', 'worker', worker.worker_id, worker_id=worker.worker_id)
        return worker
    record_failed_login(username)
    return None


def logout_worker():
    session.pop('worker_id', None)
    session.pop('worker_role', None)
    session.pop('worker_username', None)


def get_current_worker():
    worker_id = session.get('worker_id')
    if worker_id:
        worker = HealthcareWorker.query.get(worker_id)
        if worker:
            return worker

    username = request.headers.get('X-Worker-Username') or request.form.get('username')
    password = request.headers.get('X-Worker-Password') or request.form.get('password')

    if not username or not password:
        return None

    worker = HealthcareWorker.query.filter_by(username=username).first()
    if worker and check_password_hash(worker.password_hash, password):
        return worker

    return None
