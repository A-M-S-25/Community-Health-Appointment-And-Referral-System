import pytest

from app.services.referral_service import transition_referral


class ReferralStub:
    def __init__(self, status):
        self.status = status


def test_referral_can_move_from_pending_to_booked():
    referral = ReferralStub('Pending')
    transition_referral(referral, 'Booked')
    assert referral.status == 'Booked'


def test_completed_referral_cannot_be_reopened():
    with pytest.raises(ValueError, match='Cannot transition'):
        transition_referral(ReferralStub('Completed'), 'Pending')
