"""Government data source refresh tasks."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.data_sources")


@celery_app.task(name="app.tasks.data_sources.accident_data_refresh")
def accident_data_refresh() -> dict:
    """Refresh road accident data from data.gov.in."""
    logger.info("accident_data_refresh_started")
    from app.services.data_sources.accidents import AccidentDataService
    return AccidentDataService().refresh()


@celery_app.task(name="app.tasks.data_sources.ncrb_refresh")
def ncrb_refresh() -> dict:
    """Annual refresh of NCRB road accident PDF data."""
    logger.info("ncrb_refresh_started")
    from app.services.data_sources.ncrb import NCRBService
    return NCRBService().refresh()


@celery_app.task(name="app.tasks.data_sources.nhai_traffic_refresh")
def nhai_traffic_refresh() -> dict:
    """Quarterly refresh of NHAI traffic census data."""
    logger.info("nhai_traffic_refresh_started")
    from app.services.data_sources.traffic import TrafficDataService
    return TrafficDataService().refresh()


@celery_app.task(name="app.tasks.data_sources.osm_geometry_refresh")
def osm_geometry_refresh() -> dict:
    """Weekly refresh of OSM highway geometry."""
    logger.info("osm_geometry_refresh_started")
    from app.services.data_sources.osm import OSMGeometryService
    return OSMGeometryService().refresh()


@celery_app.task(name="app.tasks.data_sources.osm_notes_ingestion")
def osm_notes_ingestion() -> dict:
    """Ingest OSM notes with road damage keywords."""
    logger.info("osm_notes_ingestion_started")
    from app.services.data_sources.osm import OSMNotesService
    return OSMNotesService().ingest()
