from app.models import Referral


ALLOWED_TRANSITIONS = {
    'Draft': {'Pending', 'Cancelled'},
    'Pending': {'Accepted', 'Booked', 'Rejected', 'Cancelled'},
    'Accepted': {'Booked', 'Rejected', 'Cancelled'},
    'Booked': {'Completed', 'Cancelled'},
    'Completed': set(),
    'Cancelled': set(),
    'Rejected': set(),
}


def transition_referral(referral, new_status):
    if new_status not in ALLOWED_TRANSITIONS.get(referral.status, set()):
        raise ValueError(f'Cannot transition referral from {referral.status} to {new_status}.')
    referral.status = new_status
    return referral
