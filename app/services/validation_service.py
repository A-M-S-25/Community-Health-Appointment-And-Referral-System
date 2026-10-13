import json
import re
from datetime import datetime


class ValidationError(ValueError):
    pass


PHONE_RE = re.compile(r'^\+?[1-9]\d{8,15}$')
ALLOWED_TIER_LEVELS = {2, 3, 4, 5, 6}
MIN_REFERRAL_DESTINATION_TIER = 2
ALLOWED_ROLES = {'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'Admin'}
VALID_REFERRAL_STATUSES = {'Draft', 'Pending', 'Accepted', 'Booked', 'Completed', 'Cancelled', 'Rejected'}
REFERRAL_DESTINATION_TIERS = {
    'L1': {2, 3},
    'L2': {3, 4, 5, 6},
    'L3': {2, 4, 5, 6},
    'L4': {2, 3, 5, 6},
    'L5': {2, 3, 4, 6},
    'L6': {2, 3, 4, 5},
}


def normalize_phone(value):
    if value is None:
        return ''
    cleaned = re.sub(r'[^\d\+]', '', str(value).strip())
    if cleaned.startswith('+'):
        return '+' + re.sub(r'\D', '', cleaned[1:])
    return re.sub(r'\D', '', cleaned)


def is_valid_phone(value):
    number = normalize_phone(value)
    return bool(number) and bool(PHONE_RE.match(number))


def parse_iso_datetime(value):
    if value is None:
        raise ValidationError('Datetime is required.')

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError('Appointment datetime must be a valid ISO 8601 value.') from exc


def validate_name(value, field_name='Name'):
    text = (value or '').strip()
    if len(text) < 2:
        raise ValidationError(f'{field_name} must contain at least 2 characters.')
    return text


def validate_facility_payload(data):
    if not isinstance(data, dict):
        raise ValidationError('Facility payload must be a JSON object.')

    name = validate_name(data.get('name'), 'Facility name')
    tier_level = data.get('tier_level')
    try:
        tier_value = int(tier_level)
    except (TypeError, ValueError) as exc:
        raise ValidationError('tier_level must be an integer between 2 and 6.') from exc

    if tier_value not in ALLOWED_TIER_LEVELS:
        raise ValidationError('tier_level must be between 2 and 6.')

    capacity = data.get('capacity')
    try:
        capacity_value = int(capacity)
    except (TypeError, ValueError) as exc:
        raise ValidationError('capacity must be a positive integer.') from exc
    if capacity_value < 1:
        raise ValidationError('capacity must be a positive integer.')

    contact_info = data.get('contact_info', {})
    if isinstance(contact_info, str):
        try:
            contact_info = json.loads(contact_info)
        except json.JSONDecodeError as exc:
            raise ValidationError('contact_info must be valid JSON or an object.') from exc

    if not isinstance(contact_info, dict):
        raise ValidationError('contact_info must be a JSON object.')

    return {
        'name': name,
        'tier_level': tier_value,
        'capacity': capacity_value,
        'contact_info': json.dumps(contact_info, separators=(',', ':'))
    }


def validate_community_unit_payload(data):
    if not isinstance(data, dict):
        raise ValidationError('Community health unit payload must be a JSON object.')
    return {
        'name': validate_name(data.get('name'), 'Community health unit name'),
        'location': validate_name(data.get('location'), 'Community health unit location'),
    }


def validate_worker_payload(data):
    if not isinstance(data, dict):
        raise ValidationError('Worker payload must be a JSON object.')

    username = validate_name(data.get('username'), 'Username')
    role = str(data.get('role', '')).strip()
    if role not in ALLOWED_ROLES:
        raise ValidationError('role must be one of: L1, L2, L3, L4, L5, L6, Admin.')

    facility_value = data.get('facility_id')
    community_unit_value = data.get('community_unit_id')
    if role == 'L1':
        if facility_value is not None:
            raise ValidationError('L1 workers must not be assigned to a facility.')
        try:
            community_unit_value = int(community_unit_value)
        except (TypeError, ValueError) as exc:
            raise ValidationError('L1 workers must be assigned to a community health unit.') from exc
    elif role in {'L2', 'L3', 'L4', 'L5', 'L6'}:
        try:
            facility_value = int(facility_value)
        except (TypeError, ValueError) as exc:
            raise ValidationError('facility_id must be an integer.') from exc
        community_unit_value = None
    else:
        if facility_value is not None or community_unit_value is not None:
            raise ValidationError('Admin workers must not be assigned to a facility or community health unit.')
        facility_value = None
        community_unit_value = None

    password = data.get('password')
    if not isinstance(password, str) or len(password.strip()) < 6:
        raise ValidationError('Password must contain at least 6 characters.')

    return {
        'facility_id': facility_value,
        'community_unit_id': community_unit_value,
        'username': username,
        'role': role,
        'password': password.strip()
    }


def validate_patient_payload(data):
    if not isinstance(data, dict):
        raise ValidationError('Patient payload must be a JSON object.')

    phone_number = normalize_phone(data.get('phone_number') or data.get('phone'))
    if not is_valid_phone(phone_number):
        raise ValidationError('A valid phone number is required.')

    demographics = data.get('demographics', {}) or {}
    if not isinstance(demographics, dict):
        raise ValidationError('demographics must be a JSON object.')

    patient_name = (demographics.get('name') or '').strip()
    if not patient_name:
        raise ValidationError('Patient name is required in demographics.name.')

    return {
        'phone_number': phone_number,
        'demographics': {
            'name': patient_name,
            **demographics,
            'phone_number': phone_number
        },
        'triage_notes': (data.get('triage_notes') or data.get('triage_data') or 'No triage notes provided.').strip(),
        'destination_facility_id': data.get('destination_facility_id')
    }


def validate_referral_destination_tier(tier_level):
    try:
        tier_value = int(tier_level)
    except (TypeError, ValueError) as exc:
        raise ValidationError('Referral destination tier must be an integer.') from exc

    if tier_value < MIN_REFERRAL_DESTINATION_TIER:
        raise ValidationError(
            f'Referral destinations must be tier {MIN_REFERRAL_DESTINATION_TIER} or higher.'
        )

    return tier_value


def validate_referral_route(role, tier_level):
    tier_value = validate_referral_destination_tier(tier_level)
    if role == 'Admin':
        return tier_value
    if tier_value not in REFERRAL_DESTINATION_TIERS.get(role, set()):
        raise ValidationError(
            f'{role} clinicians cannot refer patients to a tier {tier_value} facility.'
        )
    return tier_value


def validate_referral_payload(data):
    if not isinstance(data, dict):
        raise ValidationError('Referral payload must be a JSON object.')

    triage_notes = (data.get('triage_notes') or '').strip()
    if not triage_notes:
        raise ValidationError('triage_notes cannot be empty.')

    if 'destination_facility_id' in data and data.get('destination_facility_id') is not None:
        try:
            destination_id = int(data['destination_facility_id'])
        except (TypeError, ValueError) as exc:
            raise ValidationError('destination_facility_id must be an integer.') from exc
    else:
        destination_id = None

    if destination_id is None:
        raise ValidationError('destination_facility_id is required when creating a referral.')

    return {
        'triage_notes': triage_notes,
        'destination_facility_id': destination_id
    }


def validate_appointment_payload(data):
    if not isinstance(data, dict):
        raise ValidationError('Appointment payload must be a JSON object.')

    referral_id = data.get('referral_id')
    facility_id = data.get('facility_id')
    appointment_datetime = data.get('appointment_datetime')

    try:
        referral_value = int(referral_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError('referral_id must be an integer.') from exc

    try:
        facility_value = int(facility_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError('facility_id must be an integer.') from exc

    parsed_datetime = parse_iso_datetime(appointment_datetime)

    return {
        'referral_id': referral_value,
        'facility_id': facility_value,
        'appointment_datetime': parsed_datetime
    }
