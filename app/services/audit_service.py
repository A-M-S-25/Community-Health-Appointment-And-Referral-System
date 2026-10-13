from flask import request

from app.models import AuditLog, db


def record_audit(action, resource_type, resource_id=None, metadata=None, worker_id=None):
    entry = AuditLog(
        worker_id=worker_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        metadata=metadata or {},
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
