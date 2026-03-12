"""Satellite ingestion Celery tasks."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.satellite")


@celery_app.task(name="app.tasks.satellite.sentinel2_ingestion", bind=True, max_retries=3)
def sentinel2_ingestion(self) -> dict:
    """Ingest Sentinel-2 MSI data for all highway corridors."""
    logger.info("sentinel2_ingestion_started")
    try:
        from app.services.satellite.sentinel2 import Sentinel2Ingestion
        service = Sentinel2Ingestion()
        result = service.run()
        logger.info("sentinel2_ingestion_completed", **result)
        return result
    except Exception as exc:
        logger.error("sentinel2_ingestion_failed", error=str(exc))
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.sentinel1_sar_ingestion", bind=True, max_retries=3)
def sentinel1_sar_ingestion(self) -> dict:
    """Ingest Sentinel-1 SAR data with InSAR processing."""
    logger.info("sentinel1_sar_ingestion_started")
    try:
        from app.services.satellite.sentinel1 import Sentinel1SARIngestion
        service = Sentinel1SARIngestion()
        result = service.run()
        return result
    except Exception as exc:
        logger.error("sentinel1_sar_failed", error=str(exc))
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.cartosat3_ingestion", bind=True, max_retries=3)
def cartosat3_ingestion(self) -> dict:
    """Ingest CARTOSAT-3 0.25m imagery from ISRO Bhoonidhi."""
    logger.info("cartosat3_ingestion_started")
    try:
        from app.services.satellite.isro import ISROIngestion
        service = ISROIngestion(source="CARTOSAT3")
        return service.run()
    except Exception as exc:
        logger.error("cartosat3_failed", error=str(exc))
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.cartosat2s_ingestion", bind=True, max_retries=3)
def cartosat2s_ingestion(self) -> dict:
    """Ingest CARTOSAT-2S 0.65m imagery."""
    logger.info("cartosat2s_ingestion_started")
    try:
        from app.services.satellite.isro import ISROIngestion
        service = ISROIngestion(source="CARTOSAT2S")
        return service.run()
    except Exception as exc:
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.landsat9_ingestion", bind=True, max_retries=3)
def landsat9_ingestion(self) -> dict:
    """Ingest Landsat 9 with pan-sharpening and thermal analysis."""
    logger.info("landsat9_ingestion_started")
    try:
        from app.services.satellite.landsat import LandsatIngestion
        service = LandsatIngestion(satellite="landsat9")
        return service.run()
    except Exception as exc:
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.risat2b_ingestion", bind=True, max_retries=3)
def risat2b_ingestion(self) -> dict:
    """Ingest RISAT-2B X-band SAR."""
    logger.info("risat2b_ingestion_started")
    try:
        from app.services.satellite.isro import ISROIngestion
        service = ISROIngestion(source="RISAT2B")
        return service.run()
    except Exception as exc:
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.eos04_ingestion", bind=True, max_retries=3)
def eos04_ingestion(self) -> dict:
    """Ingest EOS-04 C-band SAR for moisture detection."""
    logger.info("eos04_ingestion_started")
    try:
        from app.services.satellite.isro import ISROIngestion
        service = ISROIngestion(source="EOS04")
        return service.run()
    except Exception as exc:
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.alos2_ingestion", bind=True, max_retries=3)
def alos2_ingestion(self) -> dict:
    """Ingest ALOS-2 PALSAR-2 L-band SAR for sub-surface analysis."""
    logger.info("alos2_ingestion_started")
    try:
        from app.services.satellite.alos2 import ALOS2Ingestion
        service = ALOS2Ingestion()
        return service.run()
    except Exception as exc:
        self.retry(exc=exc, countdown=600)


@celery_app.task(name="app.tasks.satellite.modis_ingestion", bind=True, max_retries=3)
def modis_ingestion(self) -> dict:
    """Ingest MODIS thermal and cloud cover data."""
    logger.info("modis_ingestion_started")
    try:
        from app.services.satellite.modis import MODISIngestion
        service = MODISIngestion()
        return service.run()
    except Exception as exc:
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.satellite.cluster_satellite_check")
def cluster_satellite_check(latitude: float, longitude: float) -> dict:
    """Run satellite check for a confirmed mobile report cluster location."""
    logger.info("cluster_satellite_check", latitude=latitude, longitude=longitude)
    from app.services.satellite.manager import SatelliteDataManager
    manager = SatelliteDataManager()
    return manager.check_location(latitude, longitude)
