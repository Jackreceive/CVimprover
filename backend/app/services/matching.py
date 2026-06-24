import asyncio

from sqlmodel import Session

from app.database import engine
from app.models import MatchAnalysis, MatchStatus, utcnow
from app.services.llm import analyze_with_llm


def analyze_and_persist(match_id: int) -> None:
    with Session(engine) as session:
        match = session.get(MatchAnalysis, match_id)
        if match is None:
            return

        match.status = MatchStatus.running
        match.updated_at = utcnow()
        session.add(match)
        session.commit()
        session.refresh(match)

        try:
            result = asyncio.run(analyze_with_llm(match.resume.extracted_text, match.job.content))
            match.score = max(0, min(100, int(result["score"])))
            match.summary = result["summary"]
            match.skill_gaps = result["skill_gaps"]
            match.resume_suggestions = result["resume_suggestions"]
            match.raw_response = result.get("raw_response", {})
            match.status = MatchStatus.completed
            match.error_message = ""
        except Exception as exc:
            match.status = MatchStatus.failed
            match.error_message = str(exc)
        finally:
            match.updated_at = utcnow()
            session.add(match)
            session.commit()
