from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import ApplicationStatus, MatchStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ResumeRead(BaseModel):
    id: int
    filename: str
    created_at: datetime


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    company: str = Field(default="", max_length=160)
    content: str = Field(min_length=20)


class JobRead(BaseModel):
    id: int
    title: str
    company: str
    content: str
    created_at: datetime


class MatchCreate(BaseModel):
    resume_id: int
    job_id: int


class MatchRead(BaseModel):
    id: int
    resume_id: int
    job_id: int
    status: MatchStatus
    score: int | None
    summary: str
    skill_gaps: list[str]
    resume_suggestions: list[str]
    error_message: str
    created_at: datetime
    updated_at: datetime


class ApplicationCreate(BaseModel):
    job_id: int
    match_id: int | None = None
    status: ApplicationStatus = ApplicationStatus.wishlist
    notes: str = ""


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    id: int
    job_id: int
    match_id: int | None
    status: ApplicationStatus
    notes: str
    created_at: datetime
    updated_at: datetime
    job: JobRead | None = None
    match: MatchRead | None = None
