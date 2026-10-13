from app.services.security_service import (
    clear_failed_logins,
    login_is_throttled,
    record_failed_login,
)


def test_login_throttle_after_five_failures():
    username = 'test-throttle-user'
    clear_failed_logins(username)
    for _ in range(5):
        record_failed_login(username)
    assert login_is_throttled(username)
    clear_failed_logins(username)
