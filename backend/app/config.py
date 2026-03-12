"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central settings loaded from .env or environment."""

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://pothole_user:pothole_pass@db:5432/pothole_db"

    # ── Redis ─────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Security ──────────────────────────────────────────
    SECRET_KEY: str = "change-this-to-a-random-64-char-string"
    ADMIN_DEFAULT_EMAIL: str = "admin@potholeai.in"
    ADMIN_DEFAULT_PASSWORD: str = "change-this-admin-password"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # ── ESA Copernicus ────────────────────────────────────
    SENTINEL_USER: str = ""
    SENTINEL_PASS: str = ""
    CDSE_CLIENT_ID: str = ""
    CDSE_CLIENT_SECRET: str = ""

    # ── ISRO Bhoonidhi ────────────────────────────────────
    BHOONIDHI_USERNAME: str = ""
    BHOONIDHI_PASSWORD: str = ""

    # ── USGS / NASA ───────────────────────────────────────
    USGS_USERNAME: str = ""
    USGS_PASSWORD: str = ""
    USGS_M2M_API_KEY: str = ""
    NASA_EARTHDATA_USER: str = ""
    NASA_EARTHDATA_PASS: str = ""

    # ── JAXA ──────────────────────────────────────────────
    JAXA_AUIG2_USER: str = ""
    JAXA_AUIG2_PASS: str = ""

    # ── Google Earth Engine ───────────────────────────────
    GEE_SERVICE_ACCOUNT_KEY_PATH: str = ""

    # ── Gemini AI ─────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_FLASH_RPM: int = 14
    GEMINI_PRO_RPM: int = 2
    GEMINI_MAX_OUTPUT_TOKENS: int = 600
    GEMINI_TEMPERATURE: float = 0.3

    # ── PG Portal ─────────────────────────────────────────
    PG_PORTAL_USER: str = ""
    PG_PORTAL_PASS: str = ""
    PG_PORTAL_RETRY_ATTEMPTS: int = 3

    # ── Weather ───────────────────────────────────────────
    OPENWEATHERMAP_API_KEY: str = ""

    # ── Government Data ───────────────────────────────────
    DATAGOVIN_API_KEY: str = ""

    # ── Street Imagery ────────────────────────────────────
    MAPILLARY_ACCESS_TOKEN: str = ""

    # ── NRSC ──────────────────────────────────────────────
    NRSC_DATA_USERNAME: str = ""
    NRSC_DATA_PASSWORD: str = ""

    # ── Mapbox ────────────────────────────────────────────
    VITE_MAPBOX_TOKEN: str = ""

    # ── SMTP ──────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM_EMAIL: str = "pothole-system@potholeai.in"
    SMTP_FROM_NAME: str = "Pothole Intelligence System"

    # ── MinIO ─────────────────────────────────────────────
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin123"
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_BUCKET: str = "pothole-data"
    MINIO_SECURE: bool = False

    # ── SNAP ──────────────────────────────────────────────
    SNAP_HOME: str = "/opt/snap"

    # ── MLflow ────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"

    # ── Detection ─────────────────────────────────────────
    YOLO_CONFIDENCE_THRESHOLD: float = 0.55
    YOLO_NMS_IOU: float = 0.45
    TILE_SIZE: int = 640
    TILE_OVERLAP_PERCENT: int = 10
    ROAD_BUFFER_M: int = 50

    # ── Confidence Thresholds ─────────────────────────────
    AUTO_FILE_THRESHOLD: float = 0.85
    REVIEW_THRESHOLD: float = 0.65
    CCTV_SSIM_SKIP_THRESHOLD: float = 0.98

    # ── Escalation ────────────────────────────────────────
    ESCALATION_LEVEL1_DAYS: int = 30
    ESCALATION_LEVEL2_DAYS: int = 60
    ESCALATION_LEVEL3_DAYS: int = 90

    # ── Risk Score ────────────────────────────────────────
    RISK_SEVERITY_WEIGHT: float = 0.35
    RISK_ACCIDENT_WEIGHT: float = 0.30
    RISK_TRAFFIC_WEIGHT: float = 0.20
    RISK_GEOMETRY_WEIGHT: float = 0.15
    RISK_WEATHER_BOOST: float = 1.8
    RISK_ACCIDENT_RADIUS_M: int = 2000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
