"""SQLAlchemy ORM models for all 20+ database tables."""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.database import Base


# ═══════════════════════════════════════════════════════════════════
# POTHOLES — Central detection record
# ═══════════════════════════════════════════════════════════════════
class Pothole(Base):
    __tablename__ = "potholes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(8))
    area_sqm: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    depth_cm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    base_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    source_primary: Mapped[str | None] = mapped_column(String(30))
    satellite_source: Mapped[str | None] = mapped_column(String(30))
    image_path: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    road_name: Mapped[str | None] = mapped_column(Text)
    km_marker: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    district: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, default="Chhattisgarh")
    nearest_landmark: Mapped[str | None] = mapped_column(Text)
    rain_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    imd_warning_level: Mapped[str | None] = mapped_column(String(10))
    sar_first_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    alos2_detection_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    eos04_moisture_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    thermal_stress_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    drone_mission_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("drone_missions.id", ondelete="SET NULL"))
    critically_overdue: Mapped[bool] = mapped_column(Boolean, default=False)
    last_scan_date: Mapped[date | None] = mapped_column(Date)
    last_repair_status: Mapped[str | None] = mapped_column(String(20))
    detection_metadata: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    # Relationships
    complaints: Mapped[list[Complaint]] = relationship(back_populates="pothole", cascade="all, delete-orphan")
    scans: Mapped[list[Scan]] = relationship(back_populates="pothole")
    source_reports: Mapped[list[SourceReport]] = relationship(back_populates="pothole")


# ═══════════════════════════════════════════════════════════════════
# COMPLAINTS — Filed grievances
# ═══════════════════════════════════════════════════════════════════
class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pothole_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("potholes.id", ondelete="CASCADE"), nullable=False)
    complaint_text: Mapped[str] = mapped_column(Text, nullable=False)
    portal_ref: Mapped[str | None] = mapped_column(String(100))
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rain_flag: Mapped[bool | None] = mapped_column(Boolean)
    gemini_model: Mapped[str | None] = mapped_column(String(50))
    filing_proof_path: Mapped[str | None] = mapped_column(Text)
    filing_source: Mapped[str | None] = mapped_column(String(20))

    pothole: Mapped[Pothole] = relationship(back_populates="complaints")


# ═══════════════════════════════════════════════════════════════════
# SCANS — Repair verification scans
# ═══════════════════════════════════════════════════════════════════
class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pothole_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("potholes.id", ondelete="CASCADE"))
    scan_date: Mapped[date] = mapped_column(Date, nullable=False)
    before_image_path: Mapped[str | None] = mapped_column(Text)
    after_image_path: Mapped[str | None] = mapped_column(Text)
    ssim_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    siamese_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    repair_status: Mapped[str | None] = mapped_column(String(20))
    scan_source: Mapped[str | None] = mapped_column(String(30))
    scan_satellite: Mapped[str | None] = mapped_column(String(30))

    pothole: Mapped[Pothole] = relationship(back_populates="scans")


# ═══════════════════════════════════════════════════════════════════
# SOURCE REPORTS — Individual detection/corroboration events
# ═══════════════════════════════════════════════════════════════════
class SourceReport(Base):
    __tablename__ = "source_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pothole_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("potholes.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    report_type: Mapped[str | None] = mapped_column(String(20))
    jolt_magnitude: Mapped[Decimal | None] = mapped_column(Numeric(5, 3))
    gps = mapped_column(Geometry("POINT", srid=4326))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    image_path: Mapped[str | None] = mapped_column(Text)
    confidence_boost: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    device_id: Mapped[UUID | None] = mapped_column(PGUUID)
    mapillary_image_key: Mapped[str | None] = mapped_column(Text)
    drone_mission_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("drone_missions.id", ondelete="SET NULL"))

    pothole: Mapped[Pothole] = relationship(back_populates="source_reports")


# ═══════════════════════════════════════════════════════════════════
# CCTV NODES
# ═══════════════════════════════════════════════════════════════════
class CCTVNode(Base):
    __tablename__ = "cctv_nodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    camera_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    highway: Mapped[str | None] = mapped_column(String(20))
    km_marker: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    rtsp_url: Mapped[str | None] = mapped_column(Text)
    atms_zone: Mapped[str | None] = mapped_column(String(30))
    perspective_matrix: Mapped[dict | None] = mapped_column(JSONB)
    mounting_height_m: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    camera_angle_degrees: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


# ═══════════════════════════════════════════════════════════════════
# DRONE MISSIONS
# ═══════════════════════════════════════════════════════════════════
class DroneMission(Base):
    __tablename__ = "drone_missions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mission_name: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(30))
    operator: Mapped[str | None] = mapped_column(Text)
    mission_date: Mapped[date | None] = mapped_column(Date)
    highway: Mapped[str | None] = mapped_column(String(20))
    km_start: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    km_end: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    area_covered_sqkm: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    image_count: Mapped[int | None] = mapped_column(Integer)
    resolution_cm_px: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    processing_status: Mapped[str] = mapped_column(String(20), default="UPLOADED")
    detection_count: Mapped[int] = mapped_column(Integer, default=0)
    orthophoto_path: Mapped[str | None] = mapped_column(Text)
    dsm_path: Mapped[str | None] = mapped_column(Text)
    nodeodm_task_id: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ═══════════════════════════════════════════════════════════════════
# ROAD SEGMENTS
# ═══════════════════════════════════════════════════════════════════
class RoadSegment(Base):
    __tablename__ = "road_segments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    geom = mapped_column(Geometry("LINESTRING", srid=4326), nullable=False)
    highway: Mapped[str | None] = mapped_column(String(20))
    km_start: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    km_end: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    segment_length_km: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    accident_count: Mapped[int] = mapped_column(Integer, default=0)
    traffic_volume_category: Mapped[str | None] = mapped_column(String(10))
    has_curves: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blind_spot: Mapped[bool] = mapped_column(Boolean, default=False)
    slope_angle_degrees: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    priority_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    thermal_stress_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    junction_within_200m: Mapped[bool] = mapped_column(Boolean, default=False)
    data_source: Mapped[str | None] = mapped_column(String(20))


# ═══════════════════════════════════════════════════════════════════
# ROAD ACCIDENTS
# ═══════════════════════════════════════════════════════════════════
class RoadAccident(Base):
    __tablename__ = "road_accidents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    geom = mapped_column(Geometry("POINT", srid=4326))
    highway: Mapped[str | None] = mapped_column(String(20))
    km_marker: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    accident_date: Mapped[date | None] = mapped_column(Date)
    severity: Mapped[str | None] = mapped_column(String(20))
    casualty_count: Mapped[int | None] = mapped_column(Integer)
    vehicle_count: Mapped[int | None] = mapped_column(Integer)
    data_source: Mapped[str | None] = mapped_column(String(30))
    year: Mapped[int | None] = mapped_column(Integer)


# ═══════════════════════════════════════════════════════════════════
# WEATHER CACHE
# ═══════════════════════════════════════════════════════════════════
class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    grid_cell_geom = mapped_column(Geometry("POLYGON", srid=4326))
    forecast_rain_48h_mm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    gfs_rain_7d_mm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    imd_warning_level: Mapped[str | None] = mapped_column(String(10))
    open_meteo_rain_48h_mm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    forecast_date: Mapped[date | None] = mapped_column(Date)
    priority_boost_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_imd_response: Mapped[dict | None] = mapped_column(JSONB)
    raw_openmeteo_response: Mapped[dict | None] = mapped_column(JSONB)


# ═══════════════════════════════════════════════════════════════════
# SATELLITE JOBS
# ═══════════════════════════════════════════════════════════════════
class SatelliteJob(Base):
    __tablename__ = "satellite_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    highway: Mapped[str | None] = mapped_column(String(20))
    bbox: Mapped[dict | None] = mapped_column(JSONB)
    satellite_source: Mapped[str | None] = mapped_column(String(30))
    product_id: Mapped[str | None] = mapped_column(Text)
    download_date: Mapped[date | None] = mapped_column(Date)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    tile_count: Mapped[int | None] = mapped_column(Integer)
    detection_count: Mapped[int | None] = mapped_column(Integer)
    cloud_cover_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    processing_time_seconds: Mapped[int | None] = mapped_column(Integer)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ═══════════════════════════════════════════════════════════════════
# SATELLITE SOURCES — Registry of all satellite data sources
# ═══════════════════════════════════════════════════════════════════
class SatelliteSource(Base):
    __tablename__ = "satellite_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(String(20))
    resolution_m: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    repeat_cycle_days: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    last_successful_download: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    credentials_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSONB, server_default="{}")


# ═══════════════════════════════════════════════════════════════════
# SATELLITE SELECTION LOG
# ═══════════════════════════════════════════════════════════════════
class SatelliteSelectionLog(Base):
    __tablename__ = "satellite_selection_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    highway: Mapped[str | None] = mapped_column(String(20))
    selected_source: Mapped[str | None] = mapped_column(String(30))
    reason: Mapped[str | None] = mapped_column(Text)
    considered_sources: Mapped[dict | None] = mapped_column(JSONB)
    detection_cycle_date: Mapped[date | None] = mapped_column(Date)
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ═══════════════════════════════════════════════════════════════════
# SATELLITE DOWNLOAD LOG
# ═══════════════════════════════════════════════════════════════════
class SatelliteDownloadLog(Base):
    __tablename__ = "satellite_download_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str | None] = mapped_column(String(30))
    product_id: Mapped[str | None] = mapped_column(Text)
    highway: Mapped[str | None] = mapped_column(String(20))
    download_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    download_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_size_mb: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    success: Mapped[bool | None] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(Text)
    cloud_cover_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))


# ═══════════════════════════════════════════════════════════════════
# GEMINI AUDIT
# ═══════════════════════════════════════════════════════════════════
class GeminiAudit(Base):
    __tablename__ = "gemini_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pothole_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("potholes.id", ondelete="SET NULL"))
    use_case: Mapped[str | None] = mapped_column(String(30))
    prompt_text: Mapped[str | None] = mapped_column(Text)
    response_text: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(50))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)


# ═══════════════════════════════════════════════════════════════════
# ADMIN USERS
# ═══════════════════════════════════════════════════════════════════
class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="ADMIN")
    password_hash: Mapped[str | None] = mapped_column(Text)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


# ═══════════════════════════════════════════════════════════════════
# ADMIN AUDIT LOG
# ═══════════════════════════════════════════════════════════════════
class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    administrator_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("admin_users.id", ondelete="SET NULL"))
    action_type: Mapped[str | None] = mapped_column(String(50))
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[str | None] = mapped_column(Text)
    change_summary: Mapped[str | None] = mapped_column(Text)
    before_state: Mapped[dict | None] = mapped_column(JSONB)
    after_state: Mapped[dict | None] = mapped_column(JSONB)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[str | None] = mapped_column(INET)


# ═══════════════════════════════════════════════════════════════════
# TASK HISTORY
# ═══════════════════════════════════════════════════════════════════
class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    celery_task_id: Mapped[UUID | None] = mapped_column(PGUUID)
    task_name: Mapped[str | None] = mapped_column(String(100))
    queue: Mapped[str | None] = mapped_column(String(50))
    pothole_id: Mapped[int | None] = mapped_column(BigInteger)
    args_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    error_message: Mapped[str | None] = mapped_column(Text)


# ═══════════════════════════════════════════════════════════════════
# PWD OFFICERS
# ═══════════════════════════════════════════════════════════════════
class PWDOfficer(Base):
    __tablename__ = "pwd_officers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(Text)
    designation: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    highway_zone: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ═══════════════════════════════════════════════════════════════════
# GOVERNMENT CONTACTS — Escalation recipients
# ═══════════════════════════════════════════════════════════════════
class GovernmentContact(Base):
    __tablename__ = "government_contacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    authority_title: Mapped[str] = mapped_column(Text, nullable=False)
    escalation_level: Mapped[int | None] = mapped_column(Integer)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ═══════════════════════════════════════════════════════════════════
# GAMIFICATION POINTS
# ═══════════════════════════════════════════════════════════════════
class GamificationPoint(Base):
    __tablename__ = "gamification_points"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[UUID] = mapped_column(PGUUID, nullable=False)
    report_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("source_reports.id", ondelete="SET NULL"))
    points_earned: Mapped[int | None] = mapped_column(Integer)
    point_type: Mapped[str | None] = mapped_column(String(20))
    district: Mapped[str | None] = mapped_column(Text)
    earned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ═══════════════════════════════════════════════════════════════════
# MODEL REGISTRY
# ═══════════════════════════════════════════════════════════════════
class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_type: Mapped[str | None] = mapped_column(String(30))
    model_path: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(20))
    val_map50: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    val_map75: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    false_positive_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    training_images: Mapped[int | None] = mapped_column(Integer)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=False)


# ═══════════════════════════════════════════════════════════════════
# SYSTEM SETTINGS — Key-value configuration store
# ═══════════════════════════════════════════════════════════════════
class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str | None] = mapped_column(String(20))
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modified_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("admin_users.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)

