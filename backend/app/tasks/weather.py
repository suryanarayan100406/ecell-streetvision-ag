"""Weather data fetch tasks."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.weather")


@celery_app.task(name="app.tasks.weather.imd_weather_fetch")
def imd_weather_fetch() -> dict:
    """Fetch IMD district forecasts and heavy rain warnings every 3 hours."""
    logger.info("imd_weather_fetch_started")
    from app.services.weather.imd import IMDWeatherService
    return IMDWeatherService().fetch()


@celery_app.task(name="app.tasks.weather.openmeteo_weather_fetch")
def openmeteo_weather_fetch() -> dict:
    """Fetch Open-Meteo 48-hour forecasts every 6 hours."""
    logger.info("openmeteo_fetch_started")
    from app.services.weather.openmeteo import OpenMeteoService
    return OpenMeteoService().fetch()


@celery_app.task(name="app.tasks.weather.gfs_weather_fetch")
def gfs_weather_fetch() -> dict:
    """Fetch NOAA GFS 16-day precipitation forecast."""
    logger.info("gfs_fetch_started")
    from app.services.weather.gfs import GFSWeatherService
    return GFSWeatherService().fetch()


@celery_app.task(name="app.tasks.weather.owm_weather_fetch")
def owm_weather_fetch() -> dict:
    """Fetch OpenWeatherMap data as tiebreaker."""
    logger.info("owm_fetch_started")
    from app.services.weather.owm import OWMWeatherService
    return OWMWeatherService().fetch()
