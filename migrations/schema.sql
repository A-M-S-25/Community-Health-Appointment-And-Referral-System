CREATE TABLE IF NOT EXISTS facilities (
    facility_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    tier_level TINYINT UNSIGNED NOT NULL,
    capacity INT UNSIGNED NOT NULL,
    contact_info JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (facility_id),
    CONSTRAINT chk_facilities_tier CHECK (tier_level BETWEEN 2 AND 6),
    CONSTRAINT chk_facilities_capacity CHECK (capacity > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS community_health_units (
    community_unit_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (community_unit_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS healthcare_workers (
    worker_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    facility_id INT UNSIGNED NULL,
    community_unit_id INT UNSIGNED NULL,
    username VARCHAR(120) NOT NULL,
    role VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at DATETIME NULL,
    PRIMARY KEY (worker_id),
    UNIQUE KEY uq_healthcare_workers_username (username),
    KEY ix_healthcare_workers_facility (facility_id),
    CONSTRAINT fk_healthcare_workers_facility
        FOREIGN KEY (facility_id) REFERENCES facilities (facility_id),
    CONSTRAINT fk_healthcare_workers_community_unit
        FOREIGN KEY (community_unit_id) REFERENCES community_health_units (community_unit_id),
    CONSTRAINT chk_healthcare_workers_role
        CHECK (role IN ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin')),
    CONSTRAINT chk_healthcare_workers_assignment CHECK (
        (role = 'L1' AND facility_id IS NULL AND community_unit_id IS NOT NULL)
        OR (role IN ('L2', 'L3', 'L4', 'L5', 'L6') AND facility_id IS NOT NULL AND community_unit_id IS NULL)
        OR (role = 'Admin' AND facility_id IS NULL AND community_unit_id IS NULL)
    )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS patients (
    patient_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    phone_number VARCHAR(30) NOT NULL,
    demographics JSON NOT NULL,
    community_unit_id INT UNSIGNED NULL,
    triage_data JSON NOT NULL,
    PRIMARY KEY (patient_id),
    UNIQUE KEY uq_patients_phone_number (phone_number)
    ,CONSTRAINT fk_patients_community_unit
        FOREIGN KEY (community_unit_id) REFERENCES community_health_units (community_unit_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS referrals (
    referral_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    patient_id INT UNSIGNED NOT NULL,
    origin_facility_id INT UNSIGNED NULL,
    origin_community_unit_id INT UNSIGNED NULL,
    destination_facility_id INT UNSIGNED NOT NULL,
    triage_notes TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Draft',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (referral_id),
    KEY ix_referrals_patient (patient_id),
    KEY ix_referrals_origin_facility (origin_facility_id),
    KEY ix_referrals_destination_facility (destination_facility_id),
    KEY ix_referrals_status (status),
    CONSTRAINT fk_referrals_patient
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
    CONSTRAINT fk_referrals_origin_facility
        FOREIGN KEY (origin_facility_id) REFERENCES facilities (facility_id),
    CONSTRAINT fk_referrals_origin_community_unit
        FOREIGN KEY (origin_community_unit_id) REFERENCES community_health_units (community_unit_id),
    CONSTRAINT fk_referrals_destination_facility
        FOREIGN KEY (destination_facility_id) REFERENCES facilities (facility_id),
    CONSTRAINT chk_referrals_status
        CHECK (status IN ('Draft', 'Pending', 'Accepted', 'Booked', 'Completed', 'Cancelled', 'Rejected'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    referral_id INT UNSIGNED NULL,
    patient_id INT UNSIGNED NULL,
    facility_id INT UNSIGNED NOT NULL,
    appointment_datetime DATETIME NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (appointment_id),
    UNIQUE KEY uq_appointment_facility_datetime (facility_id, appointment_datetime),
    KEY ix_appointments_referral (referral_id),
    KEY ix_appointments_patient (patient_id),
    KEY ix_appointments_facility_time (facility_id, appointment_datetime),
    CONSTRAINT fk_appointments_referral
        FOREIGN KEY (referral_id) REFERENCES referrals (referral_id),
    CONSTRAINT fk_appointments_facility
        FOREIGN KEY (facility_id) REFERENCES facilities (facility_id),
    CONSTRAINT fk_appointments_patient
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
    CONSTRAINT chk_appointments_owner
        CHECK ((referral_id IS NOT NULL AND patient_id IS NULL) OR (referral_id IS NULL AND patient_id IS NOT NULL))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS patient_admissions (
    admission_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    patient_id INT UNSIGNED NOT NULL,
    facility_id INT UNSIGNED NOT NULL,
    admitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    discharged_at DATETIME NULL,
    PRIMARY KEY (admission_id),
    KEY ix_admissions_facility_active (facility_id, discharged_at),
    CONSTRAINT fk_admissions_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
    CONSTRAINT fk_admissions_facility FOREIGN KEY (facility_id) REFERENCES facilities (facility_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS appointment_slots (
    slot_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    facility_id INT UNSIGNED NOT NULL,
    appointment_datetime DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Available',
    created_by INT UNSIGNED NOT NULL,
    PRIMARY KEY (slot_id),
    UNIQUE KEY uq_slot_facility_datetime (facility_id, appointment_datetime),
    KEY ix_slots_facility_status (facility_id, status),
    CONSTRAINT fk_slots_facility FOREIGN KEY (facility_id) REFERENCES facilities (facility_id),
    CONSTRAINT fk_slots_created_by FOREIGN KEY (created_by) REFERENCES healthcare_workers (worker_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS referral_appointments (
    booking_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    referral_id INT UNSIGNED NOT NULL,
    slot_id INT UNSIGNED NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Booked',
    booked_by INT UNSIGNED NOT NULL,
    booked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (booking_id),
    UNIQUE KEY uq_referral_booking (referral_id),
    UNIQUE KEY uq_slot_booking (slot_id),
    CONSTRAINT fk_booking_referral FOREIGN KEY (referral_id) REFERENCES referrals (referral_id),
    CONSTRAINT fk_booking_slot FOREIGN KEY (slot_id) REFERENCES appointment_slots (slot_id),
    CONSTRAINT fk_booking_worker FOREIGN KEY (booked_by) REFERENCES healthcare_workers (worker_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    worker_id INT UNSIGNED NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NULL,
    metadata JSON NOT NULL,
    ip_address VARCHAR(45) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (audit_id),
    KEY ix_audit_created_at (created_at),
    KEY ix_audit_worker (worker_id),
    CONSTRAINT fk_audit_worker FOREIGN KEY (worker_id) REFERENCES healthcare_workers (worker_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sms_messages (
    message_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    recipient VARCHAR(30) NOT NULL,
    body TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    provider_message_id VARCHAR(120) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Queued',
    retry_count INT UNSIGNED NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id),
    KEY ix_sms_status (status),
    KEY ix_sms_created_at (created_at)
) ENGINE=InnoDB;
