"""Mobile app API endpoints for crowdsource reporting."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID

from app.database import get_db
from app.models import SourceReport, Pothole, GamificationPoint
from app.schemas import VisualReportCreate, VibrationReportCreate, MessageResponse

router = APIRouter()


@router.post("/visual-report", response_model=MessageResponse)
async def submit_visual_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    latitude: float = Form(...),
    longitude: float = Form(...),
    speed_kmh: float = Form(...),
    heading: float | None = Form(None),
    altitude: float | None = Form(None),
    accuracy: float | None = Form(None),
    device_id: str = Form(...),
    jolt_magnitude: float = Form(...),
    video: UploadFile = File(...),
) -> MessageResponse:
    """Submit a visual report from mounted mode with video evidence."""
    # Speed filter: ignore below 10 or above 120 km/h
    if speed_kmh < 10.0 or speed_kmh > 120.0:
        return MessageResponse(message="Speed out of valid range (10-120 km/h)", success=False)

    # Jolt threshold check
    if jolt_magnitude < 2.5:
        return MessageResponse(message="Jolt magnitude below threshold (2.5G)", success=False)

    # Save video to MinIO
    from app.utils.minio_client import upload_file
    import uuid

    video_bytes = await video.read()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    object_name = f"mobile/visual/{device_id}/{ts}.mp4"
    upload_file(object_name, video_bytes, content_type="video/mp4")

    # Create source report
    report = SourceReport(
        source="MOBILE_VISUAL",
        report_type="VISUAL",
        jolt_magnitude=jolt_magnitude,
        gps=f"SRID=4326;POINT({longitude} {latitude})",
        timestamp=datetime.now(timezone.utc),
        image_path=object_name,
        confidence_boost=1.5,
        device_id=device_id,
    )
    db.add(report)
    await db.flush()

    # Award gamification points (10 for visual report)
    points = GamificationPoint(
        device_id=device_id,
        report_id=report.id,
        points_earned=10,
        point_type="VISUAL_REPORT",
    )
    db.add(points)

    # Queue inference task
    from app.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.inference.process_mobile_report",
        args=[report.id],
        queue="inference_queue",
    )

    return MessageResponse(message="Visual report submitted successfully", success=True)


@router.post("/vibration-report", response_model=MessageResponse)
async def submit_vibration_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    report: VibrationReportCreate,
) -> MessageResponse:
    """Submit a vibration-only report from pocket mode."""
    if report.speed_kmh < 10.0 or report.speed_kmh > 120.0:
        return MessageResponse(message="Speed out of valid range", success=False)
    if report.jolt_magnitude < 2.5:
        return MessageResponse(message="Jolt below threshold", success=False)

    source_report = SourceReport(
        source="MOBILE_POCKET",
        report_type="VIBRATION",
        jolt_magnitude=report.jolt_magnitude,
        gps=f"SRID=4326;POINT({report.longitude} {report.latitude})",
        timestamp=report.timestamp,
        confidence_boost=1.2,
        device_id=str(report.device_id),
    )
    db.add(source_report)
    await db.flush()

    # Award points (3 for pocket report)
    points = GamificationPoint(
        device_id=str(report.device_id),
        report_id=source_report.id,
        points_earned=3,
        point_type="POCKET_REPORT",
    )
    db.add(points)

    # Check for cluster: 3+ unique devices within 50m in 7 days
    from datetime import timedelta
    cluster_point = ST_SetSRID(ST_MakePoint(report.longitude, report.latitude), 4326)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    cluster_count = (await db.execute(
        select(func.count(func.distinct(SourceReport.device_id)))
        .where(
            SourceReport.source == "MOBILE_POCKET",
            SourceReport.timestamp >= seven_days_ago,
            ST_DWithin(SourceReport.gps, cluster_point, 0.00045),  # ~50m
        )
    )).scalar() or 0

    if cluster_count >= 3:
        # Queue satellite check for confirmed cluster
        from app.celery_app import celery_app
        celery_app.send_task(
            "app.tasks.satellite.cluster_satellite_check",
            args=[report.latitude, report.longitude],
            queue="satellite_queue",
        )

    return MessageResponse(message="Vibration report recorded", success=True)


@router.get("/points/{device_id}")
async def get_points(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get total gamification points for a device."""
    total = (await db.execute(
        select(func.sum(GamificationPoint.points_earned))
        .where(GamificationPoint.device_id == device_id)
    )).scalar() or 0

    report_count = (await db.execute(
        select(func.count(GamificationPoint.id))
        .where(GamificationPoint.device_id == device_id)
    )).scalar() or 0

    return {"device_id": device_id, "total_points": total, "report_count": report_count}
