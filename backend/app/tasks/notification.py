"""Notification tasks — email alerts and escalations."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.notification")


@celery_app.task(name="app.tasks.notification.email_complaint_fallback")
def email_complaint_fallback(pothole_id: int) -> dict:
    """Email fallback when PG Portal filing fails after all retries."""
    logger.info("email_fallback_started", pothole_id=pothole_id)
    from app.services.filing.email_filer import EmailFiler
    filer = EmailFiler()
    return filer.send_complaint(pothole_id)


@celery_app.task(name="app.tasks.notification.send_escalation_email")
def send_escalation_email(pothole_id: int, escalation_level: int) -> dict:
    """Send escalation notification email to appropriate authority."""
    logger.info("escalation_email", pothole_id=pothole_id, level=escalation_level)
    from app.services.filing.email_filer import EmailFiler
    filer = EmailFiler()
    return filer.send_escalation(pothole_id, escalation_level)
