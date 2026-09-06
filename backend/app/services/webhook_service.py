import base64, hashlib, hmac, time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import Interview, WebhookEvent, InterviewStatus
from app.core.config import settings

def verify_signature(raw: bytes, signature: str, timestamp: str) -> bool:
    try:
        ts=int(timestamp)
        if abs(time.time()-ts)>300: return False
    except Exception: return False
    if not settings.webhook_secrets or not signature: return False
    message=f"{timestamp}.".encode()+raw
    candidates=[x.strip() for x in signature.split(",") if x.strip()]
    for secret in settings.webhook_secrets:
        digest=base64.b64encode(hmac.new(secret.encode(),message,hashlib.sha256).digest()).decode()
        if any(hmac.compare_digest(digest,c) or hmac.compare_digest("v1="+digest,c) for c in candidates): return True
    return False

def process_event(db: Session, payload: dict):
    event=payload.get("event_type") or payload.get("type") or "unknown"
    call_id=payload.get("call_id")
    request_id=payload.get("request_id")
    if call_id and db.query(WebhookEvent).filter(WebhookEvent.call_id==call_id,WebhookEvent.event_type==event).first(): return False
    db.add(WebhookEvent(event_type=event,call_id=call_id,request_id=request_id,payload=payload))
    q=db.query(Interview)
    interview=q.filter(Interview.hunar_call_id==call_id).first() if call_id else None
    if not interview and request_id: interview=q.filter(Interview.request_id==request_id).first()
    if not interview: db.commit(); return True
    status=(payload.get("status") or payload.get("lifecycle_status") or "").upper()
    mapping={"NOT_STARTED":InterviewStatus.CALL_REQUESTED,"SCHEDULED":InterviewStatus.CALL_REQUESTED,"INITIATED":InterviewStatus.INITIATED,"RINGING":InterviewStatus.RINGING,"IN_PROGRESS":InterviewStatus.IN_PROGRESS,"COMPLETED":InterviewStatus.COMPLETED,"NOT_CONNECTED":InterviewStatus.NOT_CONNECTED,"FAILED":InterviewStatus.FAILED,"CANCELLED":InterviewStatus.CANCELLED}
    if status in mapping: interview.status=mapping[status]
    if event=="call_recording_done" or payload.get("recording_url"): interview.recording_url=payload.get("recording_url") or interview.recording_url
    result=payload.get("result") or payload.get("structured_result")
    if event=="call_result_done" and result: interview.result_json=result
    if event=="call_summary":
        interview.recording_url=payload.get("recording_url") or interview.recording_url
        if payload.get("result"): interview.result_json=payload["result"]
        interview.duration_seconds=payload.get("duration_seconds") or interview.duration_seconds
    if interview.result_json:
        interview.overall_score=interview.result_json.get("overall_score")
        interview.recommendation=interview.result_json.get("recommendation")
    if interview.status==InterviewStatus.COMPLETED: interview.completed_at=datetime.now(timezone.utc)
    db.commit(); return True
