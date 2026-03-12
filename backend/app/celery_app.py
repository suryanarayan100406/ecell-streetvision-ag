"""Celery application configuration with all task queues."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "pothole_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_routes={
        "app.tasks.satellite.*": {"queue": "satellite_queue"},
        "app.tasks.inference.*": {"queue": "inference_queue"},
        "app.tasks.drone.*": {"queue": "drone_queue"},
        "app.tasks.filing.*": {"queue": "filing_queue"},
        "app.tasks.verification.*": {"queue": "verification_queue"},
        "app.tasks.notification.*": {"queue": "notification_queue"},
        "app.tasks.admin.*": {"queue": "admin_queue"},
        "app.tasks.cctv.*": {"queue": "cctv_queue"},
    },
)

# ── Celery Beat Schedule ─────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Satellite ingestion
    "satellite-s2-job": {
        "task": "app.tasks.satellite.sentinel2_ingestion",
        "schedule": crontab(hour=2, minute=0, day_of_week="*/5"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-s1-sar-job": {
        "task": "app.tasks.satellite.sentinel1_sar_ingestion",
        "schedule": crontab(hour=3, minute=0, day_of_week="*/6"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-cartosat3-job": {
        "task": "app.tasks.satellite.cartosat3_ingestion",
        "schedule": crontab(hour=2, minute=30, day_of_week="*/4"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-cartosat2s-job": {
        "task": "app.tasks.satellite.cartosat2s_ingestion",
        "schedule": crontab(hour=2, minute=45, day_of_week="*/3"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-landsat9-job": {
        "task": "app.tasks.satellite.landsat9_ingestion",
        "schedule": crontab(hour=4, minute=0, day_of_week="*/8"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-risat2b-job": {
        "task": "app.tasks.satellite.risat2b_ingestion",
        "schedule": crontab(hour=3, minute=30, day_of_week="*/2"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-eos04-job": {
        "task": "app.tasks.satellite.eos04_ingestion",
        "schedule": crontab(hour=4, minute=30, day_of_week="*/3"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-alos2-job": {
        "task": "app.tasks.satellite.alos2_ingestion",
        "schedule": crontab(hour=5, minute=0, day_of_week="*/14"),
        "options": {"queue": "satellite_queue"},
    },
    "satellite-modis-job": {
        "task": "app.tasks.satellite.modis_ingestion",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "satellite_queue"},
    },
    # Drone / Street imagery
    "oam-ingestion-job": {
        "task": "app.tasks.drone.oam_ingestion",
        "schedule": crontab(hour=1, minute=0, day_of_week="monday"),
        "options": {"queue": "drone_queue"},
    },
    "mapillary-ingestion-job": {
        "task": "app.tasks.drone.mapillary_ingestion",
        "schedule": crontab(hour=7, minute=0, day_of_week="wednesday"),
        "options": {"queue": "drone_queue"},
    },
    "kartaview-ingestion-job": {
        "task": "app.tasks.drone.kartaview_ingestion",
        "schedule": crontab(hour=7, minute=30, day_of_week="friday"),
        "options": {"queue": "drone_queue"},
    },
    # Weather
    "imd-weather-job": {
        "task": "app.tasks.weather.imd_weather_fetch",
        "schedule": crontab(minute=0, hour="*/3"),
        "options": {"queue": "satellite_queue"},
    },
    "openmeteo-weather-job": {
        "task": "app.tasks.weather.openmeteo_weather_fetch",
        "schedule": crontab(minute=30, hour="*/6"),
        "options": {"queue": "satellite_queue"},
    },
    "gfs-weather-job": {
        "task": "app.tasks.weather.gfs_weather_fetch",
        "schedule": crontab(hour="*/6", minute=15),
        "options": {"queue": "satellite_queue"},
    },
    "owm-weather-job": {
        "task": "app.tasks.weather.owm_weather_fetch",
        "schedule": crontab(hour="*/4", minute=45),
        "options": {"queue": "satellite_queue"},
    },
    # Government data
    "accident-data-refresh-job": {
        "task": "app.tasks.data_sources.accident_data_refresh",
        "schedule": crontab(hour=0, minute=0, day_of_month="1"),
        "options": {"queue": "satellite_queue"},
    },
    "ncrb-refresh-job": {
        "task": "app.tasks.data_sources.ncrb_refresh",
        "schedule": crontab(hour=0, minute=0, day_of_month="15", month_of_year="1"),
        "options": {"queue": "satellite_queue"},
    },
    "nhai-traffic-job": {
        "task": "app.tasks.data_sources.nhai_traffic_refresh",
        "schedule": crontab(hour=0, minute=0, day_of_month="1", month_of_year="*/3"),
        "options": {"queue": "satellite_queue"},
    },
    "osm-geometry-refresh-job": {
        "task": "app.tasks.data_sources.osm_geometry_refresh",
        "schedule": crontab(hour=0, minute=0, day_of_week="sunday"),
        "options": {"queue": "satellite_queue"},
    },
    "osm-notes-ingestion-job": {
        "task": "app.tasks.data_sources.osm_notes_ingestion",
        "schedule": crontab(hour=8, minute=0, day_of_week="*/2"),
        "options": {"queue": "satellite_queue"},
    },
    # Verification & Escalation
    "verify-repairs-job": {
        "task": "app.tasks.verification.verify_repairs",
        "schedule": crontab(hour=10, minute=0),
        "options": {"queue": "verification_queue"},
    },
    "escalation-check-job": {
        "task": "app.tasks.escalation.escalation_check",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "filing_queue"},
    },
    # Maintenance
    "leaderboard-refresh-job": {
        "task": "app.tasks.maintenance.leaderboard_refresh",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "admin_queue"},
    },
    "model-metrics-refresh-job": {
        "task": "app.tasks.maintenance.model_metrics_refresh",
        "schedule": crontab(hour=0, minute=0),
        "options": {"queue": "admin_queue"},
    },
    "minio-cleanup-job": {
        "task": "app.tasks.maintenance.minio_cleanup",
        "schedule": crontab(hour=3, minute=0, day_of_week="sunday"),
        "options": {"queue": "admin_queue"},
    },
    "database-backup-job": {
        "task": "app.tasks.maintenance.database_backup",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "admin_queue"},
    },
}

celery_app.autodiscover_tasks([
    "app.tasks.satellite",
    "app.tasks.inference",
    "app.tasks.drone",
    "app.tasks.filing",
    "app.tasks.verification",
    "app.tasks.escalation",
    "app.tasks.notification",
    "app.tasks.weather",
    "app.tasks.data_sources",
    "app.tasks.admin",
    "app.tasks.cctv",
    "app.tasks.maintenance",
])
