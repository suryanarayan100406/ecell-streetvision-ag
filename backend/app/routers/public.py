"""Public API endpoints — unauthenticated access."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_X, ST_Y, ST_DWithin, ST_MakePoint, ST_SetSRID

from app.database import get_db
from app.models import Pothole, Complaint, RoadSegment, GamificationPoint, SourceReport
from app.schemas import (
    PotholeResponse, PotholeListResponse, PotholeDetailResponse,
    ComplaintResponse, MessageResponse,
)

router = APIRouter()


@router.get("/potholes", response_model=PotholeListResponse)
async def list_potholes(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    highway: str | None = None,
    severity: str | None = None,
    min_risk: float | None = None,
    district: str | None = None,
) -> PotholeListResponse:
    """List all detected potholes with filters and pagination."""
    query = select(Pothole)
    count_query = select(func.count(Pothole.id))

    if highway:
        query = query.join(RoadSegment, RoadSegment.highway == highway, isouter=True)
        count_query = count_query.join(RoadSegment, RoadSegment.highway == highway, isouter=True)
    if severity:
        query = query.where(Pothole.severity == severity)
        count_query = count_query.where(Pothole.severity == severity)
    if min_risk is not None:
        query = query.where(Pothole.risk_score >= min_risk)
        count_query = count_query.where(Pothole.risk_score >= min_risk)
    if district:
        query = query.where(Pothole.district == district)
        count_query = count_query.where(Pothole.district == district)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Pothole.risk_score.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    potholes = result.scalars().all()

    items = []
    for p in potholes:
        item = PotholeResponse.model_validate(p)
        item.latitude = (await db.execute(select(ST_Y(p.geom)))).scalar()
        item.longitude = (await db.execute(select(ST_X(p.geom)))).scalar()
        items.append(item)

    return PotholeListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/potholes/{pothole_id}", response_model=PotholeDetailResponse)
async def get_pothole(
    pothole_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PotholeDetailResponse:
    """Get detailed pothole information with complaints, scans, and source reports."""
    result = await db.execute(select(Pothole).where(Pothole.id == pothole_id))
    pothole = result.scalar_one_or_none()
    if not pothole:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pothole not found")

    response = PotholeDetailResponse.model_validate(pothole)
    response.latitude = (await db.execute(select(ST_Y(pothole.geom)))).scalar()
    response.longitude = (await db.execute(select(ST_X(pothole.geom)))).scalar()
    return response


@router.get("/complaints", response_model=list[ComplaintResponse])
async def list_complaints(
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    escalation_level: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[ComplaintResponse]:
    """List all filed complaints with optional status and escalation filters."""
    query = select(Complaint)
    if status:
        query = query.where(Complaint.status == status)
    if escalation_level is not None:
        query = query.where(Complaint.escalation_level == escalation_level)
    query = query.order_by(Complaint.filed_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return [ComplaintResponse.model_validate(c) for c in result.scalars().all()]


@router.get("/analytics/summary")
async def analytics_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Public analytics summary for dashboard."""
    total_potholes = (await db.execute(select(func.count(Pothole.id)))).scalar() or 0
    total_complaints = (await db.execute(select(func.count(Complaint.id)))).scalar() or 0

    severity_counts = {}
    for sev in ["Low", "Medium", "High", "Critical"]:
        count = (await db.execute(
            select(func.count(Pothole.id)).where(Pothole.severity == sev)
        )).scalar() or 0
        severity_counts[sev] = count

    source_counts = (await db.execute(
        select(Pothole.source_primary, func.count(Pothole.id))
        .group_by(Pothole.source_primary)
    )).all()

    return {
        "total_potholes": total_potholes,
        "total_complaints": total_complaints,
        "by_severity": severity_counts,
        "by_source": {s: c for s, c in source_counts if s},
    }


@router.get("/leaderboard")
async def get_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
) -> list[dict]:
    """Public gamification leaderboard — district rankings."""
    result = await db.execute(
        select(
            GamificationPoint.district,
            func.sum(GamificationPoint.points_earned).label("total_points"),
            func.count(func.distinct(GamificationPoint.device_id)).label("contributors"),
        )
        .where(GamificationPoint.district.isnot(None))
        .group_by(GamificationPoint.district)
        .order_by(func.sum(GamificationPoint.points_earned).desc())
        .limit(limit)
    )
    return [
        {"district": row.district, "total_points": row.total_points, "contributors": row.contributors}
        for row in result.all()
    ]


@router.get("/highways")
async def list_highways(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """List monitored highways with pothole statistics."""
    result = await db.execute(
        select(
            RoadSegment.highway,
            func.count(func.distinct(RoadSegment.id)).label("segments"),
            func.sum(RoadSegment.segment_length_km).label("total_km"),
        )
        .group_by(RoadSegment.highway)
    )
    return [
        {"highway": r.highway, "segments": r.segments, "total_km": float(r.total_km or 0)}
        for r in result.all()
    ]
