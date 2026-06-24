from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

from app.config import get_settings

settings = get_settings()


def save_resume_pdf(upload: UploadFile, owner_id: int) -> tuple[str, str]:
    if upload.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF resumes are supported")

    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "resume.pdf").suffix or ".pdf"
    safe_name = f"user-{owner_id}-{uuid4().hex}{suffix}"
    path = settings.storage_dir / safe_name

    max_bytes = settings.max_upload_mb * 1024 * 1024
    written = 0
    with path.open("wb") as output:
        while chunk := upload.file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                path.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PDF is too large")
            output.write(chunk)

    return str(path), upload.filename or safe_name


def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)
