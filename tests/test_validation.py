import pytest

from app.services.validation_service import (
    ValidationError,
    validate_referral_destination_tier,
    validate_facility_payload,
    validate_patient_payload,
    validate_worker_payload,
)


def test_patient_validation_normalizes_phone_and_requires_name():
    result = validate_patient_payload({
        'phone_number': ' +254 700 123 456 ',
        'demographics': {'name': 'Amina', 'age': 29},
        'triage_notes': 'Fever',
    })
    assert result['phone_number'] == '+254700123456'
    assert result['demographics']['name'] == 'Amina'


def test_patient_validation_rejects_invalid_phone():
    with pytest.raises(ValidationError, match='valid phone'):
        validate_patient_payload({
            'phone_number': 'not-a-phone',
            'demographics': {'name': 'Amina'},
        })


def test_facility_validation_rejects_invalid_tier():
    with pytest.raises(ValidationError, match='between 2 and 6'):
        validate_facility_payload({'name': 'Facility', 'tier_level': 7})


def test_referral_destination_rejects_level_one_facility():
    with pytest.raises(ValidationError, match='tier 2 or higher'):
        validate_referral_destination_tier(1)


def test_referral_destination_accepts_tier_two_or_higher():
    assert validate_referral_destination_tier(2) == 2
    assert validate_referral_destination_tier(6) == 6


def test_referral_payload_requires_a_destination():
    from app.services.validation_service import validate_referral_payload

    with pytest.raises(ValidationError, match='destination_facility_id is required'):
        validate_referral_payload({'triage_notes': 'Critical symptoms'})


def test_admin_worker_has_no_organizational_assignment():
    result = validate_worker_payload({
        'username': 'admin',
        'password': 'secret1',
        'role': 'Admin',
    })
    assert result['facility_id'] is None
    assert result['community_unit_id'] is None


def test_clinical_worker_requires_facility():
    with pytest.raises(ValidationError, match='facility_id must be an integer'):
        validate_worker_payload({
            'username': 'nurse',
            'password': 'secret1',
            'role': 'L2',
        })


def test_community_unit_payload_requires_name_and_location():
    from app.services.validation_service import validate_community_unit_payload

    result = validate_community_unit_payload({'name': 'Kibera CHU', 'location': 'Kibera'})
    assert result == {'name': 'Kibera CHU', 'location': 'Kibera'}
