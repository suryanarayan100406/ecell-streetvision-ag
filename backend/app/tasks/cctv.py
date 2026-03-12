"""CCTV worker tasks."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.cctv")


@celery_app.task(name="app.tasks.cctv.cctv_frame_capture")
def cctv_frame_capture(atms_zone: str) -> dict:
    """Continuous frame capture worker for an ATMS zone."""
    logger.info("cctv_frame_capture_started", atms_zone=atms_zone)
    from app.services.cctv.worker import CCTVWorker
    worker = CCTVWorker(atms_zone)
    return worker.capture_cycle()
