import base64, hashlib, hmac
from app.services.webhook_service import verify_signature
from app.core.config import settings

def test_signature():
    settings.hunar_webhook_secrets="secret"
    raw=b'{"event_type":"call_summary"}'; ts="1700000000"
    # stale timestamps must be rejected
    sig=base64.b64encode(hmac.new(b"secret",f"{ts}.".encode()+raw,hashlib.sha256).digest()).decode()
    assert verify_signature(raw,sig,ts) is False
