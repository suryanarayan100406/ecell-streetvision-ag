"""Admin panel triggered tasks."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.admin")


@celery_app.task(name="app.tasks.admin.test_satellite_connection")
def test_satellite_connection(source_id: int) -> dict:
    """Test connection to a satellite data provider."""
    logger.info("test_satellite_connection", source_id=source_id)
    from app.services.satellite.manager import SatelliteDataManager
    manager = SatelliteDataManager()
    return manager.test_connection(source_id)


@celery_app.task(name="app.tasks.admin.test_cctv_connection")
def test_cctv_connection(camera_id: str) -> dict:
    """Test RTSP connection to a CCTV camera."""
    logger.info("test_cctv_connection", camera_id=camera_id)
    from app.services.cctv.connection_tester import CCTVConnectionTester
    return CCTVConnectionTester().test(camera_id)


@celery_app.task(name="app.tasks.admin.test_cctv_inference")
def test_cctv_inference(camera_id: str) -> dict:
    """Run test inference on current camera frame."""
    logger.info("test_cctv_inference", camera_id=camera_id)
    from app.services.cctv.connection_tester import CCTVConnectionTester
    return CCTVConnectionTester().test_inference(camera_id)


@celery_app.task(name="app.tasks.admin.manual_satellite_ingestion")
def manual_satellite_ingestion(source_id: int) -> dict:
    """Manually trigger satellite ingestion for a specific source."""
    logger.info("manual_satellite_ingestion", source_id=source_id)
    from app.services.satellite.manager import SatelliteDataManager
    manager = SatelliteDataManager()
    return manager.manual_ingest(source_id)
