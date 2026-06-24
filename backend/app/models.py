from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApplicationStatus(str, Enum):
    wishlist = "wishlist"
    applied = "applied"
    interviewing = "interviewing"
    offer = "offer"
    rejected = "rejected"


class MatchStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class User(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("email"),)

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False)
    full_name: str = Field(default="")
    hashed_password: str
    created_at: datetime = Field(default_factory=utcnow)

    resumes: list["Resume"] = Relationship(back_populates="owner")
    jobs: list["JobDescription"] = Relationship(back_populates="owner")


class Resume(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    filename: str
    storage_path: str
    extracted_text: str = Field(default="")
    created_at: datetime = Field(default_factory=utcnow)

    owner: User = Relationship(back_populates="resumes")
    matches: list["MatchAnalysis"] = Relationship(back_populates="resume")


class JobDescription(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    title: str
    company: str = Field(default="")
    content: str
    created_at: datetime = Field(default_factory=utcnow)

    owner: User = Relationship(back_populates="jobs")
    matches: list["MatchAnalysis"] = Relationship(back_populates="job")


class MatchAnalysis(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    resume_id: int = Field(foreign_key="resume.id", index=True)
    job_id: int = Field(foreign_key="jobdescription.id", index=True)
    status: MatchStatus = Field(default=MatchStatus.pending, index=True)
    score: int | None = Field(default=None, ge=0, le=100)
    summary: str = Field(default="")
    skill_gaps: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    resume_suggestions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    raw_response: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    error_message: str = Field(default="")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    resume: Resume = Relationship(back_populates="matches")
    job: JobDescription = Relationship(back_populates="matches")


class Application(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    job_id: int = Field(foreign_key="jobdescription.id", index=True)
    match_id: int | None = Field(default=None, foreign_key="matchanalysis.id")
    status: ApplicationStatus = Field(default=ApplicationStatus.wishlist, index=True)
    notes: str = Field(default="")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
