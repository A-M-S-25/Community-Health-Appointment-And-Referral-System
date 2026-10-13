from functools import wraps

from flask import jsonify, request

from app.services.auth_service import get_current_worker


def require_roles(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            worker = get_current_worker()
            if worker is None:
                return jsonify({'error': 'Authentication required. Please log in first.'}), 401

            if worker.role not in allowed_roles:
                return jsonify({'error': f'Role {worker.role} is not permitted for this action.'}), 403

            request.worker = worker
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
