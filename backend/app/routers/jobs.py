from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import JobDescription, User
from app.schemas import JobCreate, JobRead
from app.security import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> JobDescription:
    job = JobDescription(
        owner_id=current_user.id,
        title=payload.title,
        company=payload.company,
        content=payload.content,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.get("", response_model=list[JobRead])
def list_jobs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[JobDescription]:
    return list(
        session.exec(
            select(JobDescription).where(JobDescription.owner_id == current_user.id).order_by(JobDescription.created_at.desc())
        ).all()
    )


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> JobDescription:
    job = session.get(JobDescription, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
