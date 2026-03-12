"""Verification and repair scanning tasks."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.verification")


@celery_app.task(name="app.tasks.verification.verify_repairs")
def verify_repairs() -> dict:
    """Daily task: schedule repair verification for all due potholes."""
    logger.info("verify_repairs_started")
    from app.services.verification.repair_scanner import RepairScanner
    scanner = RepairScanner()
    return scanner.scan_all_due()


@celery_app.task(name="app.tasks.verification.repair_verification_task")
def repair_verification_task(pothole_id: int) -> dict:
    """Verify single pothole repair using Siamese CNN + SSIM."""
    logger.info("repair_verification", pothole_id=pothole_id)
    from app.services.verification.repair_scanner import RepairScanner
    scanner = RepairScanner()
    return scanner.verify_single(pothole_id)
