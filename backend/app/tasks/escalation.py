"""Escalation engine task."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.escalation")


@celery_app.task(name="app.tasks.escalation.escalation_check")
def escalation_check() -> dict:
    """Daily 6AM task: check all open complaints for escalation thresholds."""
    logger.info("escalation_check_started")
    from app.services.escalation.engine import EscalationEngine
    engine = EscalationEngine()
    return engine.run()
