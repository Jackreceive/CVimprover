from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session, select

from app.database import get_session
from app.models import Resume, User
from app.schemas import ResumeRead
from app.security import get_current_user
from app.services.storage import extract_pdf_text, save_resume_pdf

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeRead)
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Resume:
    storage_path, original_name = save_resume_pdf(file, current_user.id)
    extracted_text = extract_pdf_text(storage_path)
    resume = Resume(
        owner_id=current_user.id,
        filename=original_name,
        storage_path=storage_path,
        extracted_text=extracted_text,
    )
    session.add(resume)
    session.commit()
    session.refresh(resume)
    return resume


@router.get("", response_model=list[ResumeRead])
def list_resumes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Resume]:
    return list(session.exec(select(Resume).where(Resume.owner_id == current_user.id).order_by(Resume.created_at.desc())).all())
