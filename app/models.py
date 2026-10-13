from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.mysql import INTEGER as MYSQL_INTEGER
from sqlalchemy.orm import relationship


db = SQLAlchemy()


class Facility(db.Model):
    __tablename__ = 'facilities'

    facility_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    tier_level = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    contact_info = db.Column(db.JSON, nullable=False, default=dict)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    workers = relationship('HealthcareWorker', back_populates='facility')
    origin_referrals = relationship('Referral', foreign_keys='Referral.origin_facility_id', back_populates='origin_facility')
    destination_referrals = relationship('Referral', foreign_keys='Referral.destination_facility_id', back_populates='destination_facility')
    admissions = relationship('PatientAdmission', back_populates='facility')

    @property
    def occupied_capacity(self):
        return sum(1 for admission in self.admissions if admission.discharged_at is None)

    @property
    def available_capacity(self):
        return max(self.capacity - self.occupied_capacity, 0)


class CommunityHealthUnit(db.Model):
    __tablename__ = 'community_health_units'

    community_unit_id = db.Column(MYSQL_INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    workers = relationship('HealthcareWorker', back_populates='community_unit')
    origin_referrals = relationship('Referral', back_populates='origin_community_unit')
    patients = relationship('Patient', back_populates='community_unit')


class HealthcareWorker(db.Model):
    __tablename__ = 'healthcare_workers'
    __table_args__ = (
        CheckConstraint(
            "(role = 'L1' AND facility_id IS NULL AND community_unit_id IS NOT NULL) "
            "OR (role IN ('L2', 'L3', 'L4', 'L5', 'L6') AND facility_id IS NOT NULL AND community_unit_id IS NULL) "
            "OR (role = 'Admin' AND facility_id IS NULL AND community_unit_id IS NULL)",
            name='chk_healthcare_worker_assignment',
        ),
    )

    worker_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.facility_id'), nullable=True)
    community_unit_id = db.Column(MYSQL_INTEGER(unsigned=True), db.ForeignKey('community_health_units.community_unit_id'), nullable=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime)

    facility = relationship('Facility', back_populates='workers')
    community_unit = relationship('CommunityHealthUnit', back_populates='workers')


class Patient(db.Model):
    __tablename__ = 'patients'

    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(30), nullable=False, unique=True)
    demographics = db.Column(db.JSON, nullable=False, default=dict)
    community_unit_id = db.Column(MYSQL_INTEGER(unsigned=True), db.ForeignKey('community_health_units.community_unit_id'), nullable=True)
    triage_data = db.Column(db.JSON, nullable=False, default=dict)

    referrals = relationship('Referral', back_populates='patient')
    appointments = relationship('Appointment', back_populates='patient')
    community_unit = relationship('CommunityHealthUnit', back_populates='patients')


class Referral(db.Model):
    __tablename__ = 'referrals'

    referral_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    origin_facility_id = db.Column(db.Integer, db.ForeignKey('facilities.facility_id'), nullable=True)
    origin_community_unit_id = db.Column(MYSQL_INTEGER(unsigned=True), db.ForeignKey('community_health_units.community_unit_id'), nullable=True)
    destination_facility_id = db.Column(db.Integer, db.ForeignKey('facilities.facility_id'), nullable=False)
    triage_notes = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.String(30), nullable=False, default='Draft')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    patient = relationship('Patient', back_populates='referrals')
    origin_facility = relationship('Facility', foreign_keys=[origin_facility_id], back_populates='origin_referrals')
    origin_community_unit = relationship('CommunityHealthUnit', back_populates='origin_referrals')
    destination_facility = relationship('Facility', foreign_keys=[destination_facility_id], back_populates='destination_referrals')
    appointments = relationship('Appointment', back_populates='referral')


class Appointment(db.Model):
    __tablename__ = 'appointments'
    __table_args__ = (
        UniqueConstraint(
            'facility_id',
            'appointment_datetime',
            name='uq_appointment_facility_datetime'
        ),
    )

    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.referral_id'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.facility_id'), nullable=False)
    appointment_datetime = db.Column(db.DateTime, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)

    referral = relationship('Referral', back_populates='appointments')
    patient = relationship('Patient', back_populates='appointments')


class PatientAdmission(db.Model):
    __tablename__ = 'patient_admissions'

    admission_id = db.Column(MYSQL_INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    patient_id = db.Column(MYSQL_INTEGER(unsigned=True), db.ForeignKey('patients.patient_id'), nullable=False)
    facility_id = db.Column(MYSQL_INTEGER(unsigned=True), db.ForeignKey('facilities.facility_id'), nullable=False)
    admitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    discharged_at = db.Column(db.DateTime, nullable=True)

    patient = relationship('Patient')
    facility = relationship('Facility', back_populates='admissions')


class AppointmentSlot(db.Model):
    __tablename__ = 'appointment_slots'
    __table_args__ = (
        UniqueConstraint('facility_id', 'appointment_datetime', name='uq_slot_facility_datetime'),
    )

    slot_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.facility_id'), nullable=False)
    appointment_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Available')
    created_by = db.Column(db.Integer, db.ForeignKey('healthcare_workers.worker_id'), nullable=False)

    facility = relationship('Facility')
    creator = relationship('HealthcareWorker')
    bookings = relationship('ReferralAppointment', back_populates='slot')


class ReferralAppointment(db.Model):
    __tablename__ = 'referral_appointments'

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.referral_id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('appointment_slots.slot_id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Booked')
    booked_by = db.Column(db.Integer, db.ForeignKey('healthcare_workers.worker_id'), nullable=False)
    booked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    referral = relationship('Referral')
    slot = relationship('AppointmentSlot', back_populates='bookings')
    worker = relationship('HealthcareWorker')


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    audit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('healthcare_workers.worker_id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(100))
    metadata_json = db.Column('metadata', db.JSON, nullable=False, default=dict)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    worker = relationship('HealthcareWorker')


class SmsMessage(db.Model):
    __tablename__ = 'sms_messages'

    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient = db.Column(db.String(30), nullable=False)
    body = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), nullable=False)
    provider_message_id = db.Column(db.String(120))
    status = db.Column(db.String(30), nullable=False, default='Queued')
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
