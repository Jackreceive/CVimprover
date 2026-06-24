from app.services.matching import analyze_and_persist
from app.worker import celery_app


@celery_app.task(name="app.tasks.analyze_match")
def analyze_match(match_id: int) -> None:
    analyze_and_persist(match_id)
