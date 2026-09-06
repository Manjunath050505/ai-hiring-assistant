from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.models import Interview, Job, Candidate, InterviewCandidate, InterviewStatus
from app.schemas.schemas import InterviewCreate, CandidateStart
from app.services.interview_service import create_interview, start_interview
from app.services.webhook_service import verify_signature, process_event
from app.core.config import settings

router=APIRouter()

def serialize(i):
    c=i.candidates[0].candidate if i.candidates else None
    return {"id":i.id,"public_token":i.public_token,"status":i.status.value,"request_id":i.request_id,"hunar_call_id":i.hunar_call_id,"overall_score":i.overall_score,"recommendation":i.recommendation,"created_at":i.created_at.isoformat(),"candidate_name":c.name if c else None,"job_title":i.job.title}

@router.get("/dashboard/stats")
def stats(db:Session=Depends(get_db)):
    total=db.query(Interview).count(); completed=db.query(Interview).filter(Interview.status==InterviewStatus.COMPLETED).count(); active=db.query(Interview).filter(Interview.status.in_([InterviewStatus.CALL_REQUESTED,InterviewStatus.INITIATED,InterviewStatus.RINGING,InterviewStatus.IN_PROGRESS])).count(); scores=[x[0] for x in db.query(Interview.overall_score).filter(Interview.overall_score.isnot(None)).all()]; shortlisted=db.query(Interview).filter(Interview.recommendation.in_(["STRONG_HIRE","HIRE"])).count()
    return {"total":total,"completed":completed,"active":active,"shortlisted":shortlisted,"average_score":round(sum(scores)/len(scores),1) if scores else 0}

@router.get("/interviews")
def interviews(db:Session=Depends(get_db)): return [serialize(i) for i in db.query(Interview).order_by(Interview.created_at.desc()).all()]

@router.post("/interviews")
async def new_interview(payload:InterviewCreate,db:Session=Depends(get_db)):
    try: i=await create_interview(db,payload); return serialize(i)
    except Exception as e: db.rollback(); raise HTTPException(502,str(e))

@router.get("/interviews/{interview_id}")
def interview(interview_id:int,db:Session=Depends(get_db)):
    i=db.get(Interview,interview_id)
    if not i: raise HTTPException(404,"Interview not found")
    return {**serialize(i),"job":{"title":i.job.title,"company_name":i.job.company_name,"description":i.job.description,"skills":i.job.skills,"experience_level":i.job.experience_level},"result":i.result_json,"recording_url":i.recording_url,"duration_seconds":i.duration_seconds,"criteria":i.criteria}

@router.get("/public/interviews/{token}")
def public_interview(token:str,db:Session=Depends(get_db)):
    i=db.query(Interview).filter_by(public_token=token).first()
    if not i: raise HTTPException(404,"Interview link not found")
    return {"token":token,"job_title":i.job.title,"company_name":i.job.company_name,"status":i.status.value,"available":i.status not in {InterviewStatus.COMPLETED,InterviewStatus.CANCELLED}}

@router.post("/public/interviews/{token}/start")
async def public_start(token:str,payload:CandidateStart,db:Session=Depends(get_db)):
    i=db.query(Interview).filter_by(public_token=token).first()
    if not i: raise HTTPException(404,"Interview link not found")
    try: i=await start_interview(db,i,payload); return {"status":i.status.value,"token":token}
    except ValueError as e: raise HTTPException(400,str(e))
    except Exception as e: db.rollback(); raise HTTPException(502,"Unable to start the voice interview")

@router.get("/public/interviews/{token}/status")
def public_status(token:str,db:Session=Depends(get_db)):
    i=db.query(Interview).filter_by(public_token=token).first()
    if not i: raise HTTPException(404,"Interview link not found")
    return {"status":i.status.value,"candidate_name":i.candidates[0].candidate.name if i.candidates else None,"job_title":i.job.title}

@router.post("/webhooks/hunar")
async def hunar_webhook(request:Request,db:Session=Depends(get_db)):
    raw=await request.body(); sig=request.headers.get("X-Hunar-Signature",""); ts=request.headers.get("X-Hunar-Timestamp","")
    if not settings.hunar_mock_mode and not verify_signature(raw,sig,ts): raise HTTPException(401,"Invalid webhook signature")
    payload=await request.json(); process_event(db,payload); return {"ok":True}

@router.get("/candidates")
def candidates(db:Session=Depends(get_db)):
    return [{"id":c.id,"name":c.name,"phone_number":c.phone_number,"interviews":len(c.interviews)} for c in db.query(Candidate).order_by(Candidate.created_at.desc()).all()]
