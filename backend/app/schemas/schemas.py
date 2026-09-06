from pydantic import BaseModel, Field, field_validator
import re
from typing import Any

class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company_name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10)
    skills: str = ""
    experience_level: str = "Fresher"

class InterviewCreate(BaseModel):
    job: JobCreate
    language: str = "ENGLISH"
    voice_persona: str = "NEHA"
    interview_duration: int = Field(default=20, ge=5, le=60)
    objective: str = Field(min_length=5)
    additional_instructions: str = ""
    criteria: list[str] = Field(default_factory=lambda: ["Technical Knowledge", "Communication", "Problem Solving", "Role Fit"])

class CandidateStart(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    phone_number: str
    consent: bool
    @field_validator("phone_number")
    @classmethod
    def phone(cls, v):
        v = v.strip().replace(" ", "")
        if v.startswith("0") and len(v)==10: v = "+91" + v
        if not re.fullmatch(r"\+[1-9]\d{7,14}", v):
            raise ValueError("Use an international phone number such as +919876543210")
        return v

class InterviewOut(BaseModel):
    id: int; public_token: str; status: str; request_id: str; hunar_call_id: str | None; overall_score: float | None; recommendation: str | None; created_at: str; candidate_name: str | None; job_title: str

class ResultOut(BaseModel):
    technical_score: float | None = None
    communication_score: float | None = None
    problem_solving_score: float | None = None
    role_fit_score: float | None = None
    overall_score: float | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    summary: str = ""
    recommendation: str | None = None
    class Config: extra = "allow"
