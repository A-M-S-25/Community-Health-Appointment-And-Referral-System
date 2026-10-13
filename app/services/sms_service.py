import uuid

import requests
from flask import current_app
from app.models import SmsMessage, db


def send_sms(phone_number, message, message_type='notification'):
    record = SmsMessage(
        recipient=phone_number,
        body=message,
        message_type=message_type,
        status='Queued',
    )
    db.session.add(record)
    db.session.commit()
    payload = {
        'to': phone_number,
        'message': message,
        'api_key': current_app.config.get('SMS_API_KEY', 'demo-sms-key')
    }

    sms_url = current_app.config.get('SMS_API_URL', '')
    if sms_url:
        try:
            response = requests.post(sms_url, json=payload, timeout=5)
            if response.ok:
                record.status = 'Sent'
                record.provider_message_id = uuid.uuid4().hex
                db.session.commit()
                return {'status': 'sent', 'provider': 'gateway', 'message_id': record.provider_message_id}
            record.status = 'Failed'
            record.error_message = f'Gateway returned HTTP {response.status_code}.'
        except requests.RequestException as exc:
            record.status = 'Failed'
            record.error_message = str(exc)
    else:
        record.status = 'Queued'
        record.provider_message_id = uuid.uuid4().hex
    db.session.commit()
    return {
        'status': record.status.lower(),
        'provider': 'gateway' if sms_url else 'mock',
        'message_id': record.provider_message_id,
        'to': phone_number,
        'message': message,
    }
