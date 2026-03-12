"""Drone, Mapillary, and KartaView ingestion tasks."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.drone")


@celery_app.task(name="app.tasks.drone.oam_ingestion", bind=True, max_retries=3)
def oam_ingestion(self) -> dict:
    """Ingest community drone imagery from OpenAerialMap."""
    logger.info("oam_ingestion_started")
    try:
        from app.services.drone.oam import OAMIngestion
        service = OAMIngestion()
        return service.run()
    except Exception as exc:
        logger.error("oam_ingestion_failed", error=str(exc))
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.drone.mapillary_ingestion", bind=True, max_retries=3)
def mapillary_ingestion(self) -> dict:
    """Ingest street-level imagery from Mapillary."""
    logger.info("mapillary_ingestion_started")
    try:
        from app.services.drone.mapillary import MapillaryIngestion
        service = MapillaryIngestion()
        return service.run()
    except Exception as exc:
        logger.error("mapillary_failed", error=str(exc))
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.drone.kartaview_ingestion", bind=True, max_retries=3)
def kartaview_ingestion(self) -> dict:
    """Ingest street-level imagery from KartaView."""
    logger.info("kartaview_ingestion_started")
    try:
        from app.services.drone.kartaview import KartaViewIngestion
        service = KartaViewIngestion()
        return service.run()
    except Exception as exc:
        logger.error("kartaview_failed", error=str(exc))
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.drone.process_mission", bind=True, max_retries=2)
def process_mission(self, mission_id: int, zip_path: str) -> dict:
    """Process an uploaded drone mission through NodeODM."""
    logger.info("process_mission_started", mission_id=mission_id)
    try:
        from app.services.drone.processor import DroneProcessor
        processor = DroneProcessor()
        return processor.process(mission_id, zip_path)
    except Exception as exc:
        logger.error("mission_processing_failed", mission_id=mission_id, error=str(exc))
        self.retry(exc=exc, countdown=120)
