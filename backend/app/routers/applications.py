from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Application, ApplicationStatus, JobDescription, MatchAnalysis, User, utcnow
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.security import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])


def _serialize_application(application: Application, session: Session) -> ApplicationRead:
    job = session.get(JobDescription, application.job_id)
    match = session.get(MatchAnalysis, application.match_id) if application.match_id else None
    return ApplicationRead.model_validate(
        {
            **application.model_dump(),
            "job": job.model_dump() if job else None,
            "match": match.model_dump() if match else None,
        }
    )


@router.post("", response_model=ApplicationRead)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApplicationRead:
    job = session.get(JobDescription, payload.job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if payload.match_id:
        match = session.get(MatchAnalysis, payload.match_id)
        if not match or match.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    application = Application(
        owner_id=current_user.id,
        job_id=payload.job_id,
        match_id=payload.match_id,
        status=payload.status,
        notes=payload.notes,
    )
    session.add(application)
    session.commit()
    session.refresh(application)
    return _serialize_application(application, session)


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[ApplicationRead]:
    applications = session.exec(
        select(Application).where(Application.owner_id == current_user.id).order_by(Application.updated_at.desc())
    ).all()
    return [_serialize_application(application, session) for application in applications]


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApplicationRead:
    application = session.get(Application, application_id)
    if not application or application.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if payload.status is not None:
        application.status = payload.status
    if payload.notes is not None:
        application.notes = payload.notes
    application.updated_at = utcnow()
    session.add(application)
    session.commit()
    session.refresh(application)
    return _serialize_application(application, session)


@router.get("/stats/summary")
def application_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict[str, int]:
    applications = session.exec(select(Application).where(Application.owner_id == current_user.id)).all()
    counts = {status.value: 0 for status in ApplicationStatus}
    for application in applications:
        counts[application.status.value] += 1
    return counts
