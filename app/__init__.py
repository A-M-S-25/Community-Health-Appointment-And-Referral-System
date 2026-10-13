from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from config import Config
from app.models import Appointment, CommunityHealthUnit, Facility, HealthcareWorker, Patient, Referral, db
from app.services.auth_service import get_current_worker, login_worker, logout_worker
from app.services.security_service import get_csrf_token, valid_csrf_token


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = app.config['APP_ENV'] == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800
    db.init_app(app)

    @app.context_processor
    def inject_security_context():
        worker = get_current_worker()
        if worker is None:
            return {'csrf_token': get_csrf_token, 'current_worker': None, 'worker_affiliation': None}
        if worker.role == 'Admin':
            affiliation = 'System administrator'
        elif worker.role == 'L1':
            affiliation = worker.community_unit.name if worker.community_unit else 'Community Health Unit not assigned'
        else:
            affiliation = worker.facility.name if worker.facility else 'Facility not assigned'
        return {
            'csrf_token': get_csrf_token,
            'current_worker': worker,
            'worker_affiliation': affiliation,
        }

    @app.before_request
    def enforce_csrf():
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return None
        if request.path == '/login':
            candidate = request.form.get('csrf_token')
        else:
            candidate = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if session.get('worker_id') and not request.headers.get('X-Worker-Username'):
            if not valid_csrf_token(candidate):
                return {'error': 'CSRF validation failed.'}, 400
        return None

    if app.config['APP_ENV'] == 'development':
        with app.app_context():
            upgrade_existing_schema()
            db.create_all()
            migrate_community_unit_assignments()
            if db.engine.dialect.name == 'sqlite':
                db.session.execute(text(
                    'CREATE UNIQUE INDEX IF NOT EXISTS '
                    'uq_appointment_facility_datetime '
                    'ON appointments (facility_id, appointment_datetime)'
                ))
                db.session.commit()
            seed_demo_data()

    from app.routes.patients import patients_bp
    from app.routes.facilities import facilities_bp
    from app.routes.appointments import appointments_bp
    from app.routes.admin import admin_bp
    from app.routes.details import details_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(patients_bp)
    app.register_blueprint(facilities_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(details_bp)
    app.register_blueprint(profile_bp)

    @app.route('/')
    def index():
        worker = get_current_worker()
        if worker:
            if worker.role == 'Admin':
                return redirect(url_for('admin.admin_dashboard_page'))
            return redirect(url_for('referrals_page'))
        return render_template('login.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        if request.method == 'POST':
            if not valid_csrf_token(request.form.get('csrf_token')):
                return render_template('login.html', error='Your session token is invalid. Refresh and try again.'), 400
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password') or ''
            worker = login_worker(username, password)
            if worker is None:
                return render_template('login.html', error='Invalid username or password.'), 401
            if worker.role == 'Admin':
                return redirect(url_for('admin.admin_dashboard_page'))
            return redirect(url_for('referrals_page'))
        return render_template('login.html')

    @app.route('/logout')
    def logout_page():
        logout_worker()
        return redirect(url_for('login_page'))

    @app.route('/register')
    def register_page():
        worker = get_current_worker()
        if worker is None:
            return redirect(url_for('login_page'))
        if worker.role not in ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin'):
            return 'This page is restricted to authenticated system users.', 403
        return render_template('registration.html')

    @app.route('/patients/search')
    def patient_search_page():
        worker = get_current_worker()
        if worker is None:
            return redirect(url_for('login_page'))
        if worker.role not in ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin'):
            return 'Patient lookup is restricted to authenticated system users.', 403
        return render_template('patient_search.html')

    @app.route('/referrals')
    def referrals_page():
        worker = get_current_worker()
        if worker is None:
            return redirect(url_for('login_page'))
        return render_template('referrals.html')

    @app.route('/appointments')
    def appointments_page():
        worker = get_current_worker()
        if worker is None:
            return redirect(url_for('login_page'))
        if worker.role not in ('L2', 'L3', 'L4', 'L5', 'L6', 'Admin'):
            return 'Appointments are restricted to tier 2-6 clinicians and administrators.', 403
        return render_template('appointments.html')

    @app.route('/patients/<int:patient_id>/triage')
    def patient_triage_page(patient_id):
        worker = get_current_worker()
        if worker is None:
            return redirect(url_for('login_page'))
        if worker.role not in ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin'):
            return 'Authentication required.', 403
        patient = Patient.query.get_or_404(patient_id)
        if worker.role == 'L1' and patient.community_unit_id != worker.community_unit_id:
            return 'You are not permitted to manage this patient triage record.', 403
        return render_template('patient_triage.html', patient=patient)

    return app


def upgrade_existing_schema():
    """Add fields introduced after the initial development schema."""
    inspector = inspect(db.engine)
    dialect = db.engine.dialect.name

    def columns(table):
        return {column['name'] for column in inspector.get_columns(table)}

    if 'facilities' in inspector.get_table_names() and 'capacity' not in columns('facilities'):
        if dialect == 'mysql':
            db.session.execute(text(
                'ALTER TABLE facilities ADD COLUMN capacity INT UNSIGNED NOT NULL DEFAULT 1'
            ))
        else:
            db.session.execute(text(
                'ALTER TABLE facilities ADD COLUMN capacity INTEGER NOT NULL DEFAULT 1'
            ))
    if 'healthcare_workers' in inspector.get_table_names() and 'community_unit_id' not in columns('healthcare_workers'):
        column_type = 'INT UNSIGNED' if dialect == 'mysql' else 'INTEGER'
        db.session.execute(text(
            f'ALTER TABLE healthcare_workers ADD COLUMN community_unit_id {column_type} NULL'
        ))
    if dialect == 'mysql' and 'healthcare_workers' in inspector.get_table_names():
        db.session.execute(text(
            'ALTER TABLE healthcare_workers MODIFY facility_id INT UNSIGNED NULL'
        ))
    if 'referrals' in inspector.get_table_names() and 'origin_community_unit_id' not in columns('referrals'):
        column_type = 'INT UNSIGNED' if dialect == 'mysql' else 'INTEGER'
        db.session.execute(text(
            f'ALTER TABLE referrals ADD COLUMN origin_community_unit_id {column_type} NULL'
        ))
    if 'patients' in inspector.get_table_names():
        patient_columns = columns('patients')
        if 'community_unit_id' not in patient_columns:
            column_type = 'INT UNSIGNED' if dialect == 'mysql' else 'INTEGER'
            db.session.execute(text(
                f'ALTER TABLE patients ADD COLUMN community_unit_id {column_type} NULL'
            ))
        if 'triage_data' not in patient_columns:
            triage_type = 'JSON' if dialect == 'mysql' else 'JSON'
            db.session.execute(text(
                f'ALTER TABLE patients ADD COLUMN triage_data {triage_type} NOT NULL DEFAULT \'{{}}\''
            ))
    if dialect == 'mysql' and 'referrals' in inspector.get_table_names():
        db.session.execute(text(
            'ALTER TABLE referrals MODIFY origin_facility_id INT UNSIGNED NULL'
        ))
        db.session.execute(text(
            'ALTER TABLE referrals DROP CONSTRAINT chk_referrals_status'
        ))
        db.session.execute(text(
            "ALTER TABLE referrals ADD CONSTRAINT chk_referrals_status CHECK "
            "(status IN ('Draft', 'Pending', 'Accepted', 'Booked', 'Completed', 'Cancelled', 'Rejected'))"
        ))
    db.session.commit()


def migrate_community_unit_assignments():
    """Move legacy tier-one facility assignments into a community health unit."""
    legacy_facilities = Facility.query.filter_by(tier_level=1).all()
    if not legacy_facilities:
        HealthcareWorker.query.filter_by(role='Admin').update({
            HealthcareWorker.facility_id: None,
            HealthcareWorker.community_unit_id: None,
        }, synchronize_session=False)
        db.session.commit()
        return

    unit = CommunityHealthUnit.query.first()
    if unit is None:
        unit = CommunityHealthUnit(name='Community Health Unit', location='Unspecified')
        db.session.add(unit)
        db.session.flush()

    legacy_ids = [facility.facility_id for facility in legacy_facilities]
    HealthcareWorker.query.filter(
        HealthcareWorker.facility_id.in_(legacy_ids),
        HealthcareWorker.role == 'L1',
    ).update({
        HealthcareWorker.facility_id: None,
        HealthcareWorker.community_unit_id: unit.community_unit_id,
    }, synchronize_session=False)
    Referral.query.filter(Referral.origin_facility_id.in_(legacy_ids)).update({
        Referral.origin_facility_id: None,
        Referral.origin_community_unit_id: unit.community_unit_id,
    }, synchronize_session=False)
    HealthcareWorker.query.filter_by(role='Admin').update({
        HealthcareWorker.facility_id: None,
        HealthcareWorker.community_unit_id: None,
    }, synchronize_session=False)
    db.session.commit()


def seed_demo_data():
    if Facility.query.count() == 0:
        facilities = [
            Facility(name='Muguga Health Centre', tier_level=2, capacity=50, contact_info='{"location": "Kibera"}'),
            Facility(name='Kisumu County Referral Hospital', tier_level=5, capacity=200, contact_info='{"location": "Kisumu"}'),
            Facility(name='Kenyatta National Hospital', tier_level=6, capacity=500, contact_info='{"location": "Nairobi"}'),
        ]
        db.session.add_all(facilities)
        db.session.commit()

    if HealthcareWorker.query.count() == 0:
        facility_map = {f.name: f for f in Facility.query.all()}
        community_unit = CommunityHealthUnit(name='Kibera Community Unit', location='Kibera')
        db.session.add(community_unit)
        db.session.flush()
        workers = [
            HealthcareWorker(
                facility_id=None,
                community_unit_id=community_unit.community_unit_id,
                username='chp01',
                role='L1',
                password_hash=generate_password_hash('demo123')
            ),
            HealthcareWorker(
                facility_id=facility_map['Muguga Health Centre'].facility_id,
                username='nurse02',
                role='L2',
                password_hash=generate_password_hash('demo123')
            ),
            HealthcareWorker(
                facility_id=None,
                community_unit_id=None,
                username='admin01',
                role='Admin',
                password_hash=generate_password_hash('demo123')
            ),
        ]
        db.session.add_all(workers)
        db.session.commit()

    if Patient.query.count() == 0:
        patient = Patient(phone_number='+254700000001', demographics={'name': 'Jane Doe', 'age': 34})
        db.session.add(patient)
        db.session.commit()

        referral = Referral(
            patient_id=patient.patient_id,
            origin_community_unit_id=CommunityHealthUnit.query.first().community_unit_id,
            destination_facility_id=Facility.query.filter_by(tier_level=5).first().facility_id,
            triage_notes='Fever and cough for 3 days',
            status='Pending'
        )
        db.session.add(referral)
        db.session.commit()

        appointment = Appointment(
            referral_id=referral.referral_id,
            facility_id=Facility.query.filter_by(tier_level=5).first().facility_id,
            appointment_datetime=datetime(2026, 10, 15, 10, 30),
            is_locked=False
        )
        db.session.add(appointment)
        db.session.commit()
