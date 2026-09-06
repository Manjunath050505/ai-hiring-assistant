import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import Interview, Job, Candidate, InterviewCandidate, InterviewStatus
from app.services.hunar_client import HunarClient, HunarError
from app.core.config import settings

def interviewer_prompt(job: Job, objective: str, criteria: list[str], additional: str):
    return f"""You are a professional AI interviewer for {job.company_name}. Conduct a structured interview for the {job.title} role.\nCandidate: {{candidate_name}}.\nJob description: {job.description}\nRequired skills: {job.skills}\nExperience: {job.experience_level}\nObjective: {objective}\nEvaluation criteria: {', '.join(criteria)}\nAdditional instructions: {additional}\nAsk one question at a time, use relevant follow-ups, do not coach or reveal scoring, remain professional, and end politely. Return structured evaluation with scores 0-10, strengths, weaknesses, summary and recommendation."""

async def create_interview(db: Session, payload):
    job=Job(**payload.job.model_dump()); db.add(job); db.flush()
    prompt=interviewer_prompt(job,payload.objective,payload.criteria,payload.additional_instructions)
    schema={"type":"object","properties":{"technical_score":{"type":"number"},"communication_score":{"type":"number"},"problem_solving_score":{"type":"number"},"role_fit_score":{"type":"number"},"overall_score":{"type":"number"},"strengths":{"type":"array","items":{"type":"string"}},"weaknesses":{"type":"array","items":{"type":"string"}},"summary":{"type":"string"},"recommendation":{"type":"string","enum":["STRONG_HIRE","HIRE","MAYBE","REJECT"]}},"required":["overall_score","summary","recommendation"]}
    agent=await HunarClient().create_agent({"name":f"AI Interviewer - {job.title}","language":payload.language,"voice_persona":payload.voice_persona,"agent_prompt":prompt,"objective":payload.objective,"introduction":f"Hello, I am your AI interviewer for the {job.title} position at {job.company_name}.","result_prompt":"Evaluate the candidate objectively and return the structured result.","result_schema":schema})
    interview=Interview(job_id=job.id,hunar_agent_id=agent.get("id"),language=payload.language,voice_persona=payload.voice_persona,interview_prompt=prompt,criteria=payload.criteria,status=InterviewStatus.PUBLISHED)
    db.add(interview); db.commit(); db.refresh(interview)
    return interview

async def start_interview(db: Session, interview: Interview, payload):
    if not payload.consent: raise ValueError("Consent is required")
    if interview.status in {InterviewStatus.COMPLETED,InterviewStatus.CANCELLED}: raise ValueError("This interview is no longer available")
    candidate=db.query(Candidate).filter(Candidate.phone_number==payload.phone_number).first()
    if not candidate:
        candidate=Candidate(name=payload.name,phone_number=payload.phone_number); db.add(candidate); db.flush()
    else: candidate.name=payload.name
    link=db.query(InterviewCandidate).filter_by(interview_id=interview.id,candidate_id=candidate.id).first()
    if link and interview.status not in {InterviewStatus.PUBLISHED,InterviewStatus.CREATED}: raise ValueError("This interview has already been started")
    if not link:
        link=InterviewCandidate(interview_id=interview.id,candidate_id=candidate.id,consent=True); db.add(link)
    interview.status=InterviewStatus.CALL_REQUESTED; interview.started_at=datetime.now(timezone.utc)
    custom={"candidate_name":candidate.name,"mobile_number":candidate.phone_number,"job_title":interview.job.title,"job_description":interview.job.description,"skills":interview.job.skills,"experience_level":interview.job.experience_level,"company_name":interview.job.company_name,"interview_questions":"Ask adaptive role-relevant questions.","interview_id":str(interview.id)}
    try:
        call=await HunarClient().create_call({"agent_id":interview.hunar_agent_id,"callee_name":candidate.name,"mobile_number":candidate.phone_number,"custom_data":custom,"request_id":interview.request_id,"timezone":"Asia/Kolkata"})
    except HunarError as e:
        interview.status=InterviewStatus.FAILED; db.commit(); raise
    interview.hunar_call_id=call.get("id"); interview.status=InterviewStatus.INITIATED if not settings.hunar_mock_mode else InterviewStatus.RINGING
    db.commit(); return interview
