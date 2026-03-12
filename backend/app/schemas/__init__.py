"""Pydantic v2 schemas for all API request/response models."""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ═══════════════════════════════════════════════════════════════════
# POTHOLE SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class PotholeBase(BaseModel):
    severity: str | None = None
    area_sqm: Decimal | None = None
    depth_cm: Decimal | None = None
    risk_score: Decimal | None = None
    confidence_score: Decimal | None = None
    source_primary: str | None = None
    satellite_source: str | None = None
    road_name: str | None = None
    km_marker: Decimal | None = None
    district: str | None = None
    state: str = "Chhattisgarh"
    nearest_landmark: str | None = None
    rain_flag: bool = False
    critically_overdue: bool = False


class PotholeResponse(PotholeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latitude: float | None = None
    longitude: float | None = None
    detected_at: datetime
    image_path: str | None = None
    base_risk_score: Decimal | None = None
    imd_warning_level: str | None = None
    sar_first_detected_at: datetime | None = None
    alos2_detection_date: datetime | None = None
    eos04_moisture_flag: bool = False
    thermal_stress_flag: bool = False
    last_scan_date: date | None = None
    last_repair_status: str | None = None
    drone_mission_id: int | None = None
    detection_metadata: dict = Field(default_factory=dict)


class PotholeListResponse(BaseModel):
    items: list[PotholeResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════════
# COMPLAINT SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class ComplaintBase(BaseModel):
    complaint_text: str
    status: str = "PENDING"
    escalation_level: int = 0


class ComplaintResponse(ComplaintBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pothole_id: int
    portal_ref: str | None = None
    filed_at: datetime | None = None
    escalated_at: datetime | None = None
    rain_flag: bool | None = None
    gemini_model: str | None = None
    filing_proof_path: str | None = None
    filing_source: str | None = None


# ═══════════════════════════════════════════════════════════════════
# SCAN SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pothole_id: int
    scan_date: date
    before_image_path: str | None = None
    after_image_path: str | None = None
    ssim_score: Decimal | None = None
    siamese_score: Decimal | None = None
    repair_status: str | None = None
    scan_source: str | None = None
    scan_satellite: str | None = None


# ═══════════════════════════════════════════════════════════════════
# SOURCE REPORT SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class SourceReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pothole_id: int
    source: str
    report_type: str | None = None
    jolt_magnitude: Decimal | None = None
    timestamp: datetime
    image_path: str | None = None
    confidence_boost: Decimal | None = None
    device_id: UUID | None = None
    mapillary_image_key: str | None = None
    drone_mission_id: int | None = None


class PotholeDetailResponse(PotholeResponse):
    complaints: list[ComplaintResponse] = Field(default_factory=list)
    scans: list[ScanResponse] = Field(default_factory=list)
    source_reports: list[SourceReportResponse] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# MOBILE REPORT SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class VisualReportCreate(BaseModel):
    latitude: float
    longitude: float
    speed_kmh: float
    heading: float | None = None
    altitude: float | None = None
    accuracy: float | None = None
    device_id: UUID
    jolt_magnitude: float


class VibrationReportCreate(BaseModel):
    latitude: float
    longitude: float
    speed_kmh: float
    jolt_magnitude: float
    device_id: UUID
    timestamp: datetime


# ═══════════════════════════════════════════════════════════════════
# CCTV SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class CCTVNodeBase(BaseModel):
    camera_id: str
    latitude: float
    longitude: float
    highway: str | None = None
    km_marker: Decimal | None = None
    rtsp_url: str | None = None
    atms_zone: str | None = None
    mounting_height_m: Decimal | None = None
    camera_angle_degrees: Decimal | None = None


class CCTVNodeCreate(CCTVNodeBase):
    pass


class CCTVNodeUpdate(BaseModel):
    rtsp_url: str | None = None
    atms_zone: str | None = None
    mounting_height_m: Decimal | None = None
    camera_angle_degrees: Decimal | None = None
    status: str | None = None
    perspective_matrix: dict | None = None


class CCTVNodeResponse(CCTVNodeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    perspective_matrix: dict | None = None
    last_active: datetime | None = None
    status: str


# ═══════════════════════════════════════════════════════════════════
# DRONE MISSION SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class DroneMissionCreate(BaseModel):
    mission_name: str
    source: str
    operator: str | None = None
    mission_date: date | None = None
    highway: str | None = None
    km_start: Decimal | None = None
    km_end: Decimal | None = None


class DroneMissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mission_name: str | None = None
    source: str | None = None
    operator: str | None = None
    mission_date: date | None = None
    highway: str | None = None
    km_start: Decimal | None = None
    km_end: Decimal | None = None
    area_covered_sqkm: Decimal | None = None
    image_count: int | None = None
    resolution_cm_px: Decimal | None = None
    processing_status: str
    detection_count: int
    orthophoto_path: str | None = None
    dsm_path: str | None = None
    submitted_at: datetime | None = None
    completed_at: datetime | None = None


# ═══════════════════════════════════════════════════════════════════
# SATELLITE SOURCE SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class SatelliteSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    display_name: str | None = None
    source_type: str | None = None
    resolution_m: Decimal | None = None
    repeat_cycle_days: int | None = None
    status: str
    last_successful_download: datetime | None = None
    last_attempt: datetime | None = None
    last_error: str | None = None
    credentials_configured: bool
    config: dict = Field(default_factory=dict)


class SatelliteSourceUpdate(BaseModel):
    status: str | None = None
    config: dict | None = None
    credentials_configured: bool | None = None


# ═══════════════════════════════════════════════════════════════════
# ADMIN AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AdminUserResponse


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None = None
    role: str
    last_login: datetime | None = None
    status: str


class AdminUserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str = "ADMIN"


# ═══════════════════════════════════════════════════════════════════
# SYSTEM HEALTH / OVERVIEW SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class ComponentHealth(BaseModel):
    name: str
    status: str  # HEALTHY, DEGRADED, ERROR, INACTIVE
    last_error: str | None = None
    last_success: datetime | None = None


class SystemOverview(BaseModel):
    total_potholes: int
    open_complaints: dict[str, int]  # by escalation level
    complaints_filed_today: int
    verified_repairs_month: int
    component_health: list[ComponentHealth]


class ActivityEvent(BaseModel):
    id: int
    event_type: str
    description: str
    resource_id: int | None = None
    resource_type: str | None = None
    timestamp: datetime
    source: str | None = None


# ═══════════════════════════════════════════════════════════════════
# SCHEDULER SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class ScheduledTaskResponse(BaseModel):
    task_name: str
    description: str | None = None
    schedule: str
    next_run: datetime | None = None
    last_run: datetime | None = None
    last_status: str | None = None
    last_duration_seconds: float | None = None
    enabled: bool


# ═══════════════════════════════════════════════════════════════════
# WEATHER SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class WeatherResponse(BaseModel):
    forecast_rain_48h_mm: Decimal | None = None
    gfs_rain_7d_mm: Decimal | None = None
    imd_warning_level: str | None = None
    open_meteo_rain_48h_mm: Decimal | None = None
    forecast_date: date | None = None
    checked_at: datetime | None = None


# ═══════════════════════════════════════════════════════════════════
# GEMINI AUDIT SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class GeminiAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pothole_id: int | None = None
    use_case: str | None = None
    prompt_text: str | None = None
    response_text: str | None = None
    model_name: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    called_at: datetime | None = None
    success: bool
    error_message: str | None = None


# ═══════════════════════════════════════════════════════════════════
# TASK HISTORY SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class TaskHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    celery_task_id: UUID | None = None
    task_name: str | None = None
    queue: str | None = None
    pothole_id: int | None = None
    args_summary: str | None = None
    status: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: Decimal | None = None
    error_message: str | None = None


# ═══════════════════════════════════════════════════════════════════
# GENERIC RESPONSE
# ═══════════════════════════════════════════════════════════════════
class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
