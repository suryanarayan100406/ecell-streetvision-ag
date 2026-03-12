"""Admin Control Panel API endpoints — full system management."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    AdminUser, AdminAuditLog, Pothole, Complaint, Scan, SourceReport,
    CCTVNode, DroneMission, SatelliteSource, SatelliteJob, SatelliteSelectionLog,
    SatelliteDownloadLog, GeminiAudit, TaskHistory, ModelRegistry,
    SystemSetting, WeatherCache, RoadSegment, GovernmentContact,
)
from app.schemas import (
    AdminLoginRequest, AdminLoginResponse, AdminUserResponse, AdminUserCreate,
    CCTVNodeCreate, CCTVNodeUpdate, CCTVNodeResponse,
    DroneMissionCreate, DroneMissionResponse,
    SatelliteSourceResponse, SatelliteSourceUpdate,
    GeminiAuditResponse, TaskHistoryResponse,
    SystemOverview, ComponentHealth, ActivityEvent,
    MessageResponse,
)
from app.utils.auth import (
    get_current_admin, require_admin_role, require_super_admin,
    hash_password, verify_password, create_access_token, create_refresh_token,
)
from app.config import settings

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════
@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminLoginResponse:
    """Authenticate admin user and return JWT token."""
    result = await db.execute(select(AdminUser).where(AdminUser.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account is inactive")

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    token = create_access_token({"sub": str(user.id), "role": user.role})

    # Log login
    audit = AdminAuditLog(
        administrator_id=user.id,
        action_type="LOGIN",
        resource_type="admin_users",
        resource_id=str(user.id),
        change_summary="Admin login",
    )
    db.add(audit)

    return AdminLoginResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AdminUserResponse.model_validate(user),
    )


# ═══════════════════════════════════════════════════════════════════
# SYSTEM OVERVIEW
# ═══════════════════════════════════════════════════════════════════
@router.get("/overview", response_model=SystemOverview)
async def system_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> SystemOverview:
    """System overview with component health and summary metrics."""
    total_potholes = (await db.execute(select(func.count(Pothole.id)))).scalar() or 0

    # Open complaints by escalation level
    escalation_counts = {}
    for level in range(4):
        count = (await db.execute(
            select(func.count(Complaint.id))
            .where(Complaint.escalation_level == level, Complaint.status != "REPAIRED")
        )).scalar() or 0
        escalation_counts[f"level_{level}"] = count

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    complaints_today = (await db.execute(
        select(func.count(Complaint.id)).where(Complaint.filed_at >= today_start)
    )).scalar() or 0

    month_start = today_start.replace(day=1)
    repairs_month = (await db.execute(
        select(func.count(Scan.id))
        .where(Scan.repair_status == "Repaired", Scan.scan_date >= month_start.date())
    )).scalar() or 0

    # Component health from satellite sources
    satellite_health = []
    sources = (await db.execute(select(SatelliteSource))).scalars().all()
    for src in sources:
        status_val = "HEALTHY" if src.status == "ACTIVE" and not src.last_error else (
            "ERROR" if src.last_error else (
                "INACTIVE" if src.status == "INACTIVE" else "DEGRADED"
            )
        )
        satellite_health.append(ComponentHealth(
            name=src.display_name or src.source_name,
            status=status_val,
            last_error=src.last_error,
            last_success=src.last_successful_download,
        ))

    return SystemOverview(
        total_potholes=total_potholes,
        open_complaints=escalation_counts,
        complaints_filed_today=complaints_today,
        verified_repairs_month=repairs_month,
        component_health=satellite_health,
    )


@router.get("/activity-feed", response_model=list[ActivityEvent])
async def activity_feed(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    limit: int = Query(100, ge=1, le=500),
) -> list[ActivityEvent]:
    """Get the last N pipeline events for real-time activity feed."""
    events: list[ActivityEvent] = []

    # Recent detections
    detections = await db.execute(
        select(Pothole).order_by(Pothole.detected_at.desc()).limit(limit // 3)
    )
    for p in detections.scalars().all():
        events.append(ActivityEvent(
            id=p.id,
            event_type="DETECTION",
            description=f"{p.severity} pothole detected on {p.road_name or 'Unknown road'} via {p.source_primary}",
            resource_id=p.id,
            resource_type="pothole",
            timestamp=p.detected_at,
            source=p.source_primary,
        ))

    # Recent complaints
    complaints = await db.execute(
        select(Complaint).order_by(Complaint.filed_at.desc().nullslast()).limit(limit // 3)
    )
    for c in complaints.scalars().all():
        events.append(ActivityEvent(
            id=c.id,
            event_type="COMPLAINT_FILED",
            description=f"Complaint filed for pothole #{c.pothole_id} — ref: {c.portal_ref or 'pending'}",
            resource_id=c.pothole_id,
            resource_type="complaint",
            timestamp=c.filed_at or c.escalated_at or datetime.now(timezone.utc),
            source="PG_PORTAL",
        ))

    events.sort(key=lambda e: e.timestamp, reverse=True)
    return events[:limit]


# ═══════════════════════════════════════════════════════════════════
# SATELLITE SOURCES MANAGEMENT
# ═══════════════════════════════════════════════════════════════════
@router.get("/satellites", response_model=list[SatelliteSourceResponse])
async def list_satellite_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> list[SatelliteSourceResponse]:
    """List all configured satellite sources."""
    result = await db.execute(select(SatelliteSource).order_by(SatelliteSource.source_name))
    return [SatelliteSourceResponse.model_validate(s) for s in result.scalars().all()]


@router.put("/satellites/{source_id}", response_model=SatelliteSourceResponse)
async def update_satellite_source(
    source_id: int,
    update_data: SatelliteSourceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
) -> SatelliteSourceResponse:
    """Update a satellite source configuration."""
    result = await db.execute(select(SatelliteSource).where(SatelliteSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Satellite source not found")

    before_state = {"status": source.status, "config": source.config}

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    # Audit log
    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="UPDATE_SATELLITE_SOURCE",
        resource_type="satellite_sources",
        resource_id=str(source_id),
        change_summary=f"Updated satellite source {source.source_name}",
        before_state=before_state,
        after_state=update_data.model_dump(exclude_unset=True),
    )
    db.add(audit)

    return SatelliteSourceResponse.model_validate(source)


@router.post("/satellites/{source_id}/test", response_model=MessageResponse)
async def test_satellite_connection(
    source_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> MessageResponse:
    """Test connection to a satellite data source."""
    result = await db.execute(select(SatelliteSource).where(SatelliteSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Queue a test task
    from app.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.admin.test_satellite_connection",
        args=[source_id],
        queue="admin_queue",
    )
    return MessageResponse(message=f"Connection test queued for {source.source_name}")


@router.post("/satellites/{source_id}/trigger", response_model=MessageResponse)
async def trigger_satellite_ingestion(
    source_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
) -> MessageResponse:
    """Manually trigger a satellite ingestion job."""
    result = await db.execute(select(SatelliteSource).where(SatelliteSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    from app.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.admin.manual_satellite_ingestion",
        args=[source_id],
        queue="satellite_queue",
    )

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="TRIGGER_SATELLITE_INGESTION",
        resource_type="satellite_sources",
        resource_id=str(source_id),
        change_summary=f"Manual trigger for {source.source_name}",
    )
    db.add(audit)

    return MessageResponse(message=f"Ingestion job queued for {source.source_name}")


@router.get("/satellites/{source_id}/downloads")
async def satellite_download_history(
    source_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    limit: int = Query(20, ge=1, le=100),
) -> list[dict]:
    """Get download history for a satellite source."""
    source = (await db.execute(select(SatelliteSource).where(SatelliteSource.id == source_id))).scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await db.execute(
        select(SatelliteDownloadLog)
        .where(SatelliteDownloadLog.source == source.source_name)
        .order_by(SatelliteDownloadLog.download_started_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": d.id, "product_id": d.product_id, "highway": d.highway,
            "started_at": d.download_started_at.isoformat() if d.download_started_at else None,
            "completed_at": d.download_completed_at.isoformat() if d.download_completed_at else None,
            "file_size_mb": float(d.file_size_mb) if d.file_size_mb else None,
            "success": d.success, "error": d.error_message,
            "cloud_cover": float(d.cloud_cover_pct) if d.cloud_cover_pct else None,
        }
        for d in result.scalars().all()
    ]


@router.get("/satellites/selection-log")
async def satellite_selection_log(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """Get satellite selection decision log."""
    result = await db.execute(
        select(SatelliteSelectionLog)
        .order_by(SatelliteSelectionLog.selected_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": s.id, "highway": s.highway, "selected_source": s.selected_source,
            "reason": s.reason, "considered_sources": s.considered_sources,
            "date": s.detection_cycle_date.isoformat() if s.detection_cycle_date else None,
            "selected_at": s.selected_at.isoformat() if s.selected_at else None,
        }
        for s in result.scalars().all()
    ]


# ═══════════════════════════════════════════════════════════════════
# CCTV CAMERA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════
@router.get("/cctv", response_model=list[CCTVNodeResponse])
async def list_cctv_cameras(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    highway: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
) -> list[CCTVNodeResponse]:
    """List all CCTV cameras with optional filters."""
    query = select(CCTVNode)
    if highway:
        query = query.where(CCTVNode.highway == highway)
    if status_filter:
        query = query.where(CCTVNode.status == status_filter)
    result = await db.execute(query.order_by(CCTVNode.camera_id))
    return [CCTVNodeResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/cctv", response_model=CCTVNodeResponse)
async def add_cctv_camera(
    camera: CCTVNodeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
) -> CCTVNodeResponse:
    """Add a new CCTV camera."""
    # Check uniqueness
    existing = (await db.execute(
        select(CCTVNode).where(CCTVNode.camera_id == camera.camera_id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Camera ID already exists")

    node = CCTVNode(
        camera_id=camera.camera_id,
        geom=f"SRID=4326;POINT({camera.longitude} {camera.latitude})",
        highway=camera.highway,
        km_marker=camera.km_marker,
        rtsp_url=camera.rtsp_url,
        atms_zone=camera.atms_zone,
        mounting_height_m=camera.mounting_height_m,
        camera_angle_degrees=camera.camera_angle_degrees,
        status="TESTING",
    )
    db.add(node)
    await db.flush()

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="ADD_CCTV_CAMERA",
        resource_type="cctv_nodes",
        resource_id=str(node.id),
        change_summary=f"Added camera {camera.camera_id}",
        after_state=camera.model_dump(),
    )
    db.add(audit)

    return CCTVNodeResponse.model_validate(node)


@router.put("/cctv/{camera_id}", response_model=CCTVNodeResponse)
async def update_cctv_camera(
    camera_id: str,
    update_data: CCTVNodeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
) -> CCTVNodeResponse:
    """Update an existing CCTV camera."""
    result = await db.execute(select(CCTVNode).where(CCTVNode.camera_id == camera_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Camera not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(node, field, value)

    return CCTVNodeResponse.model_validate(node)


@router.post("/cctv/{camera_id}/test", response_model=MessageResponse)
async def test_cctv_connection(
    camera_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> MessageResponse:
    """Test connection to a CCTV camera."""
    result = await db.execute(select(CCTVNode).where(CCTVNode.camera_id == camera_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Camera not found")

    from app.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.admin.test_cctv_connection",
        args=[camera_id],
        queue="admin_queue",
    )
    return MessageResponse(message=f"Connection test queued for camera {camera_id}")


@router.post("/cctv/{camera_id}/test-inference", response_model=MessageResponse)
async def test_cctv_inference(
    camera_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> MessageResponse:
    """Run test YOLOv8 inference on current camera frame."""
    from app.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.admin.test_cctv_inference",
        args=[camera_id],
        queue="inference_queue",
    )
    return MessageResponse(message=f"Test inference queued for camera {camera_id}")


# ═══════════════════════════════════════════════════════════════════
# DRONE MISSIONS MANAGEMENT
# ═══════════════════════════════════════════════════════════════════
@router.get("/drones", response_model=list[DroneMissionResponse])
async def list_drone_missions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    highway: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
) -> list[DroneMissionResponse]:
    """List all drone missions."""
    query = select(DroneMission)
    if highway:
        query = query.where(DroneMission.highway == highway)
    if status_filter:
        query = query.where(DroneMission.processing_status == status_filter)
    result = await db.execute(query.order_by(DroneMission.mission_date.desc().nullslast()))
    return [DroneMissionResponse.model_validate(m) for m in result.scalars().all()]


@router.post("/drones/upload", response_model=DroneMissionResponse)
async def upload_drone_mission(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
    mission_name: str = Query(...),
    source: str = Query(...),
    operator: str | None = Query(None),
    highway: str | None = Query(None),
    km_start: float | None = Query(None),
    km_end: float | None = Query(None),
    images: UploadFile = File(...),
) -> DroneMissionResponse:
    """Upload a new drone mission with images ZIP."""
    from app.utils.minio_client import upload_file
    import uuid

    mission = DroneMission(
        mission_name=mission_name,
        source=source,
        operator=operator,
        highway=highway,
        km_start=km_start,
        km_end=km_end,
        processing_status="UPLOADED",
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(mission)
    await db.flush()

    # Save uploaded ZIP to MinIO
    content = await images.read()
    object_name = f"drone/missions/{mission.id}/raw/{images.filename}"
    upload_file(object_name, content, content_type="application/zip")

    # Queue processing
    from app.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.drone.process_mission",
        args=[mission.id, object_name],
        queue="drone_queue",
    )

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="UPLOAD_DRONE_MISSION",
        resource_type="drone_missions",
        resource_id=str(mission.id),
        change_summary=f"Uploaded drone mission: {mission_name}",
    )
    db.add(audit)

    return DroneMissionResponse.model_validate(mission)


# ═══════════════════════════════════════════════════════════════════
# DETECTION REVIEW
# ═══════════════════════════════════════════════════════════════════
@router.get("/review")
async def list_review_potholes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    highway: str | None = None,
) -> dict:
    """List potholes pending review (confidence 0.65-0.84)."""
    query = select(Pothole).where(
        Pothole.confidence_score >= 0.65,
        Pothole.confidence_score < 0.85,
    )
    if severity:
        query = query.where(Pothole.severity == severity)

    total = (await db.execute(
        select(func.count(Pothole.id)).where(
            Pothole.confidence_score >= 0.65, Pothole.confidence_score < 0.85,
        )
    )).scalar() or 0

    query = query.order_by(Pothole.risk_score.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)

    items = []
    for p in result.scalars().all():
        from geoalchemy2.functions import ST_X, ST_Y
        lat = (await db.execute(select(ST_Y(p.geom)))).scalar()
        lon = (await db.execute(select(ST_X(p.geom)))).scalar()
        items.append({
            "id": p.id, "severity": p.severity, "risk_score": float(p.risk_score) if p.risk_score else None,
            "confidence_score": float(p.confidence_score) if p.confidence_score else None,
            "source_primary": p.source_primary, "road_name": p.road_name,
            "km_marker": float(p.km_marker) if p.km_marker else None,
            "latitude": lat, "longitude": lon,
            "image_path": p.image_path, "detected_at": p.detected_at.isoformat(),
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/review/{pothole_id}/accept", response_model=MessageResponse)
async def accept_detection(
    pothole_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> MessageResponse:
    """Accept a detection and move to filing queue."""
    result = await db.execute(select(Pothole).where(Pothole.id == pothole_id))
    pothole = result.scalar_one_or_none()
    if not pothole:
        raise HTTPException(status_code=404, detail="Pothole not found")

    pothole.confidence_score = max(float(pothole.confidence_score or 0), 0.85)

    from app.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.filing.generate_and_file_complaint",
        args=[pothole_id],
        queue="filing_queue",
    )

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="ACCEPT_DETECTION",
        resource_type="potholes",
        resource_id=str(pothole_id),
        change_summary="Detection accepted, queued for filing",
    )
    db.add(audit)

    return MessageResponse(message=f"Pothole #{pothole_id} accepted and queued for filing")


@router.post("/review/{pothole_id}/reject", response_model=MessageResponse)
async def reject_detection(
    pothole_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> MessageResponse:
    """Reject a detection as false positive."""
    result = await db.execute(select(Pothole).where(Pothole.id == pothole_id))
    pothole = result.scalar_one_or_none()
    if not pothole:
        raise HTTPException(status_code=404, detail="Pothole not found")

    pothole.confidence_score = 0
    pothole.detection_metadata = {**pothole.detection_metadata, "false_positive": True, "rejected_by": current_user.id}

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="REJECT_DETECTION",
        resource_type="potholes",
        resource_id=str(pothole_id),
        change_summary="Detection rejected as false positive",
    )
    db.add(audit)

    return MessageResponse(message=f"Pothole #{pothole_id} rejected as false positive")


# ═══════════════════════════════════════════════════════════════════
# PIPELINE MONITOR
# ═══════════════════════════════════════════════════════════════════
@router.get("/pipeline/task-history")
async def task_history_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    task_name: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
) -> dict:
    """Get paginated task history."""
    query = select(TaskHistory)
    count_query = select(func.count(TaskHistory.id))

    if task_name:
        query = query.where(TaskHistory.task_name.ilike(f"%{task_name}%"))
        count_query = count_query.where(TaskHistory.task_name.ilike(f"%{task_name}%"))
    if status_filter:
        query = query.where(TaskHistory.status == status_filter)
        count_query = count_query.where(TaskHistory.status == status_filter)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(TaskHistory.started_at.desc().nullslast())
        .offset((page - 1) * page_size).limit(page_size)
    )

    return {
        "items": [TaskHistoryResponse.model_validate(t).model_dump() for t in result.scalars().all()],
        "total": total, "page": page, "page_size": page_size,
    }


# ═══════════════════════════════════════════════════════════════════
# MODEL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════
@router.get("/models")
async def list_models(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> list[dict]:
    """List all registered models."""
    result = await db.execute(select(ModelRegistry).order_by(ModelRegistry.trained_at.desc().nullslast()))
    return [
        {
            "id": m.id, "model_type": m.model_type, "version": m.version,
            "val_map50": float(m.val_map50) if m.val_map50 else None,
            "val_map75": float(m.val_map75) if m.val_map75 else None,
            "false_positive_rate": float(m.false_positive_rate) if m.false_positive_rate else None,
            "training_images": m.training_images,
            "trained_at": m.trained_at.isoformat() if m.trained_at else None,
            "active": m.active,
        }
        for m in result.scalars().all()
    ]


@router.post("/models/{model_id}/promote", response_model=MessageResponse)
async def promote_model(
    model_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
) -> MessageResponse:
    """Promote a model to active production use."""
    result = await db.execute(select(ModelRegistry).where(ModelRegistry.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Deactivate all models of same type
    await db.execute(
        update(ModelRegistry)
        .where(ModelRegistry.model_type == model.model_type)
        .values(active=False)
    )
    model.active = True

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="PROMOTE_MODEL",
        resource_type="model_registry",
        resource_id=str(model_id),
        change_summary=f"Promoted {model.model_type} v{model.version} to production",
    )
    db.add(audit)

    return MessageResponse(message=f"Model {model.model_type} v{model.version} promoted to production")


# ═══════════════════════════════════════════════════════════════════
# SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════════
@router.get("/settings")
async def get_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> list[dict]:
    """Get all system settings."""
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    return [
        {
            "id": s.id, "key": s.key, "value": s.value, "value_type": s.value_type,
            "last_modified": s.last_modified.isoformat() if s.last_modified else None,
            "description": s.description,
        }
        for s in result.scalars().all()
    ]


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    value: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
) -> dict:
    """Update a system setting."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    old_value = setting.value
    setting.value = value
    setting.last_modified = datetime.now(timezone.utc)
    setting.modified_by = current_user.id

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="UPDATE_SETTING",
        resource_type="system_settings",
        resource_id=key,
        change_summary=f"Setting {key}: {old_value} → {value}",
        before_state={"value": old_value},
        after_state={"value": value},
    )
    db.add(audit)

    return {"key": key, "value": value, "updated": True}


# ═══════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════
@router.get("/users", response_model=list[AdminUserResponse])
async def list_admin_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
) -> list[AdminUserResponse]:
    """List all admin users."""
    result = await db.execute(select(AdminUser).order_by(AdminUser.email))
    return [AdminUserResponse.model_validate(u) for u in result.scalars().all()]


@router.post("/users", response_model=AdminUserResponse)
async def create_admin_user(
    user_data: AdminUserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(require_super_admin)],
) -> AdminUserResponse:
    """Create a new admin user."""
    existing = (await db.execute(
        select(AdminUser).where(AdminUser.email == user_data.email)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = AdminUser(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        password_hash=hash_password(user_data.password),
        status="ACTIVE",
    )
    db.add(user)
    await db.flush()

    return AdminUserResponse.model_validate(user)


# ═══════════════════════════════════════════════════════════════════
# LOGS & AUDIT
# ═══════════════════════════════════════════════════════════════════
@router.get("/audit-log")
async def get_audit_log(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action_type: str | None = None,
) -> dict:
    """Get admin audit log with pagination."""
    query = select(AdminAuditLog)
    count_query = select(func.count(AdminAuditLog.id))

    if action_type:
        query = query.where(AdminAuditLog.action_type == action_type)
        count_query = count_query.where(AdminAuditLog.action_type == action_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(AdminAuditLog.performed_at.desc().nullslast())
        .offset((page - 1) * page_size).limit(page_size)
    )

    items = []
    for a in result.scalars().all():
        items.append({
            "id": a.id, "administrator_id": a.administrator_id,
            "action_type": a.action_type, "resource_type": a.resource_type,
            "resource_id": a.resource_id, "change_summary": a.change_summary,
            "before_state": a.before_state, "after_state": a.after_state,
            "performed_at": a.performed_at.isoformat() if a.performed_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/gemini-audit")
async def get_gemini_audit(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    pothole_id: int | None = None,
) -> dict:
    """Get Gemini API call audit log."""
    query = select(GeminiAudit)
    count_query = select(func.count(GeminiAudit.id))

    if pothole_id:
        query = query.where(GeminiAudit.pothole_id == pothole_id)
        count_query = count_query.where(GeminiAudit.pothole_id == pothole_id)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(GeminiAudit.called_at.desc().nullslast())
        .offset((page - 1) * page_size).limit(page_size)
    )

    return {
        "items": [GeminiAuditResponse.model_validate(g).model_dump() for g in result.scalars().all()],
        "total": total, "page": page, "page_size": page_size,
    }


# ═══════════════════════════════════════════════════════════════════
# SCHEDULER
# ═══════════════════════════════════════════════════════════════════
@router.get("/scheduler/tasks")
async def list_scheduled_tasks(
    current_user: Annotated[AdminUser, Depends(get_current_admin)],
) -> list[dict]:
    """List all Celery beat scheduled tasks."""
    from app.celery_app import celery_app

    tasks = []
    for name, config in celery_app.conf.beat_schedule.items():
        tasks.append({
            "task_name": name,
            "task_function": config.get("task"),
            "schedule": str(config.get("schedule")),
            "queue": config.get("options", {}).get("queue", "default"),
            "enabled": True,
        })
    return tasks


@router.post("/scheduler/{task_name}/trigger", response_model=MessageResponse)
async def trigger_scheduled_task(
    task_name: str,
    current_user: Annotated[AdminUser, Depends(require_admin_role)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Manually trigger a scheduled task."""
    from app.celery_app import celery_app

    if task_name not in celery_app.conf.beat_schedule:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    config = celery_app.conf.beat_schedule[task_name]
    task_func = config["task"]
    queue = config.get("options", {}).get("queue", "default")

    celery_app.send_task(task_func, queue=queue)

    audit = AdminAuditLog(
        administrator_id=current_user.id,
        action_type="TRIGGER_SCHEDULED_TASK",
        resource_type="scheduler",
        resource_id=task_name,
        change_summary=f"Manual trigger: {task_name}",
    )
    db.add(audit)

    return MessageResponse(message=f"Task '{task_name}' triggered successfully")
