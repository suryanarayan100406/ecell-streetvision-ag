"""Dashboard API endpoints for operator-level access."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Pothole, Complaint, Scan, SourceReport

router = APIRouter()


@router.get("/kanban")
async def complaint_kanban(
    db: Annotated[AsyncSession, Depends(get_db)],
    highway: str | None = None,
) -> dict[str, list]:
    """Get complaints organised in kanban columns by status."""
    query = select(Complaint, Pothole).join(Pothole, Complaint.pothole_id == Pothole.id)
    if highway:
        query = query.where(Pothole.road_name.ilike(f"%{highway}%"))

    result = await db.execute(query.order_by(Pothole.risk_score.desc().nullslast()))
    rows = result.all()

    kanban: dict[str, list] = {
        "DETECTED": [],
        "FILED": [],
        "ACKNOWLEDGED": [],
        "IN_PROGRESS": [],
        "REPAIRED": [],
    }

    for complaint, pothole in rows:
        card = {
            "complaint_id": complaint.id,
            "pothole_id": pothole.id,
            "road_name": pothole.road_name,
            "km_marker": float(pothole.km_marker) if pothole.km_marker else None,
            "severity": pothole.severity,
            "risk_score": float(pothole.risk_score) if pothole.risk_score else None,
            "status": complaint.status,
            "escalation_level": complaint.escalation_level,
            "filed_at": complaint.filed_at.isoformat() if complaint.filed_at else None,
            "portal_ref": complaint.portal_ref,
            "source_primary": pothole.source_primary,
            "rain_flag": pothole.rain_flag,
            "critically_overdue": pothole.critically_overdue,
        }
        column = complaint.status if complaint.status in kanban else "DETECTED"
        kanban[column].append(card)

    return kanban


@router.get("/detections-by-source")
async def detections_by_source(
    db: Annotated[AsyncSession, Depends(get_db)],
    hours: int = Query(24, ge=1, le=168),
) -> list[dict]:
    """Detections per hour broken down by source for the last N hours."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(
            func.date_trunc("hour", Pothole.detected_at).label("hour"),
            Pothole.source_primary,
            func.count(Pothole.id).label("count"),
        )
        .where(Pothole.detected_at >= since)
        .group_by("hour", Pothole.source_primary)
        .order_by("hour")
    )

    return [
        {"hour": row.hour.isoformat(), "source": row.source_primary, "count": row.count}
        for row in result.all()
    ]


@router.get("/repair-timeline/{pothole_id}")
async def repair_timeline(
    pothole_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """Get the complete chronological timeline for a pothole."""
    events: list[dict] = []

    # Detection event
    pothole_result = await db.execute(select(Pothole).where(Pothole.id == pothole_id))
    pothole = pothole_result.scalar_one_or_none()
    if pothole:
        events.append({
            "type": "DETECTION",
            "timestamp": pothole.detected_at.isoformat(),
            "details": {
                "source": pothole.source_primary,
                "satellite": pothole.satellite_source,
                "severity": pothole.severity,
                "confidence": float(pothole.confidence_score) if pothole.confidence_score else None,
            },
        })

    # Source reports
    reports = await db.execute(
        select(SourceReport).where(SourceReport.pothole_id == pothole_id).order_by(SourceReport.timestamp)
    )
    for report in reports.scalars().all():
        events.append({
            "type": "SOURCE_REPORT",
            "timestamp": report.timestamp.isoformat(),
            "details": {"source": report.source, "confidence_boost": float(report.confidence_boost) if report.confidence_boost else None},
        })

    # Complaints
    complaints = await db.execute(
        select(Complaint).where(Complaint.pothole_id == pothole_id).order_by(Complaint.filed_at)
    )
    for c in complaints.scalars().all():
        events.append({
            "type": "COMPLAINT_FILED" if c.escalation_level == 0 else f"ESCALATION_L{c.escalation_level}",
            "timestamp": (c.filed_at or c.escalated_at or pothole.detected_at).isoformat(),
            "details": {"portal_ref": c.portal_ref, "status": c.status, "level": c.escalation_level},
        })

    # Scans
    scans = await db.execute(
        select(Scan).where(Scan.pothole_id == pothole_id).order_by(Scan.scan_date)
    )
    for s in scans.scalars().all():
        events.append({
            "type": "REPAIR_SCAN",
            "timestamp": s.scan_date.isoformat(),
            "details": {
                "repair_status": s.repair_status,
                "ssim_score": float(s.ssim_score) if s.ssim_score else None,
                "siamese_score": float(s.siamese_score) if s.siamese_score else None,
            },
        })

    events.sort(key=lambda e: e["timestamp"])
    return events
