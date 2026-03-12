"""3-tier escalation engine."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("services.escalation")


class EscalationEngine:
    """Check all open complaints for escalation thresholds and trigger escalation pipeline."""

    THRESHOLDS = {
        1: ("ESCALATION_LEVEL1_DAYS", "District Collector"),
        2: ("ESCALATION_LEVEL2_DAYS", "Principal Secretary PWD"),
        3: ("ESCALATION_LEVEL3_DAYS", "Secretary MoRTH"),
    }

    def run(self) -> dict:
        """Run escalation check across all open complaints."""
        logger.info("escalation_engine_started")

        # In production, queries database for open complaints
        # and checks days_since_filing against thresholds
        escalated_count = 0
        checked_count = 0

        # Placeholder for actual implementation
        return {
            "status": "completed",
            "checked": checked_count,
            "escalated": escalated_count,
        }

    def check_complaint(self, complaint_data: dict) -> int | None:
        """Check if a complaint should be escalated. Returns new level or None."""
        days_open = complaint_data.get("days_since_filing", 0)
        current_level = complaint_data.get("escalation_level", 0)

        if current_level >= 3:
            return None  # Already at max level

        if days_open >= settings.ESCALATION_LEVEL3_DAYS and current_level < 3:
            return 3
        elif days_open >= settings.ESCALATION_LEVEL2_DAYS and current_level < 2:
            return 2
        elif days_open >= settings.ESCALATION_LEVEL1_DAYS and current_level < 1:
            return 1

        return None

    def escalate(self, pothole_id: int, new_level: int) -> dict:
        """Execute escalation: fresh evidence + new complaint + email."""
        logger.info("escalating", pothole_id=pothole_id, new_level=new_level)

        from app.celery_app import celery_app

        # Step 1: Queue repair verification for fresh evidence
        celery_app.send_task(
            "app.tasks.verification.repair_verification_task",
            args=[pothole_id],
            queue="verification_queue",
        )

        # Step 2: Generate escalation complaint via Gemini
        celery_app.send_task(
            "app.tasks.filing.gemini_escalation_task",
            args=[pothole_id, new_level],
            queue="filing_queue",
        )

        # Step 3: Send escalation email
        celery_app.send_task(
            "app.tasks.notification.send_escalation_email",
            args=[pothole_id, new_level],
            queue="notification_queue",
        )

        if new_level == 3:
            logger.warning("critically_overdue_escalation", pothole_id=pothole_id)

        return {"pothole_id": pothole_id, "escalated_to": new_level}
