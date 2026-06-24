from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import JobDescription, MatchAnalysis, Resume, User
from app.schemas import MatchCreate, MatchRead
from app.security import get_current_user
from app.tasks import analyze_match

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=MatchRead)
def create_match(
    payload: MatchCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MatchAnalysis:
    resume = session.get(Resume, payload.resume_id)
    job = session.get(JobDescription, payload.job_id)
    if not resume or resume.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not resume.extracted_text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No readable text extracted from PDF")

    match = MatchAnalysis(owner_id=current_user.id, resume_id=resume.id, job_id=job.id)
    session.add(match)
    session.commit()
    session.refresh(match)
    analyze_match.delay(match.id)
    return match


@router.get("", response_model=list[MatchRead])
def list_matches(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[MatchAnalysis]:
    return list(
        session.exec(
            select(MatchAnalysis).where(MatchAnalysis.owner_id == current_user.id).order_by(MatchAnalysis.created_at.desc())
        ).all()
    )


@router.get("/{match_id}", response_model=MatchRead)
def get_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MatchAnalysis:
    match = session.get(MatchAnalysis, match_id)
    if not match or match.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match
