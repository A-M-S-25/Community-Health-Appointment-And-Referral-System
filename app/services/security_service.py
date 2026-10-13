import secrets
import time

from flask import session


def get_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
    return token


def valid_csrf_token(candidate):
    token = session.get('csrf_token')
    return bool(token and candidate and secrets.compare_digest(token, candidate))


_failed_logins = {}


def login_is_throttled(username):
    item = _failed_logins.get(username)
    if not item:
        return False
    failures, blocked_until = item
    if blocked_until <= time.time():
        _failed_logins.pop(username, None)
        return False
    return failures >= 5


def record_failed_login(username):
    failures, _ = _failed_logins.get(username, (0, 0))
    failures += 1
    blocked_until = time.time() + 300 if failures >= 5 else 0
    _failed_logins[username] = (failures, blocked_until)


def clear_failed_logins(username):
    _failed_logins.pop(username, None)
