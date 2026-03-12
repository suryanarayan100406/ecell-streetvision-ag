"""Complaint filing tasks — Gemini generation and Playwright PG Portal filing."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.filing")


@celery_app.task(name="app.tasks.filing.generate_and_file_complaint", bind=True, max_retries=3)
def generate_and_file_complaint(self, pothole_id: int) -> dict:
    """Generate complaint via Gemini and file on PG Portal."""
    logger.info("generate_and_file_started", pothole_id=pothole_id)
    try:
        # Step 1: Generate complaint text via Gemini
        from app.services.gemini.complaint_generator import ComplaintGenerator
        generator = ComplaintGenerator()
        complaint_data = generator.generate(pothole_id)

        # Step 2: File on PG Portal via Playwright
        from app.services.filing.pg_portal import PGPortalFiler
        filer = PGPortalFiler()
        result = filer.file_complaint(pothole_id, complaint_data)

        logger.info("complaint_filed_successfully", pothole_id=pothole_id, portal_ref=result.get("portal_ref"))
        return result
    except Exception as exc:
        logger.error("complaint_filing_failed", pothole_id=pothole_id, error=str(exc))
        if self.request.retries >= self.max_retries:
            # Email fallback after all retries exhausted
            celery_app.send_task(
                "app.tasks.notification.email_complaint_fallback",
                args=[pothole_id],
                queue="notification_queue",
            )
        self.retry(exc=exc, countdown=[30, 90, 270][min(self.request.retries, 2)])


@celery_app.task(name="app.tasks.filing.gemini_escalation_task", bind=True, max_retries=3)
def gemini_escalation_task(self, pothole_id: int, escalation_level: int) -> dict:
    """Generate escalation complaint text via Gemini."""
    logger.info("escalation_complaint_started", pothole_id=pothole_id, level=escalation_level)
    try:
        from app.services.gemini.complaint_generator import ComplaintGenerator
        generator = ComplaintGenerator()
        return generator.generate_escalation(pothole_id, escalation_level)
    except Exception as exc:
        logger.error("escalation_generation_failed", error=str(exc))
        self.retry(exc=exc, countdown=60)
