"""Seed the database with realistic demo data for Chhattisgarh highways."""

import asyncio
import random
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal

from sqlalchemy import select, text
from app.database import engine, Base, async_session_factory
from app.models import (
    Pothole, Complaint, Scan, SourceReport, SatelliteSource, SatelliteDownloadLog,
    SatelliteSelectionLog, CCTVNode, DroneMission, ModelRegistry, SystemSetting,
    TaskHistory, GeminiAudit, AdminAuditLog, AdminUser,
)
from app.utils.auth import hash_password
from app.config import settings

# ── Real GPS coordinates along Chhattisgarh National Highways ───────
NH_ROUTES = {
    "NH-30": [
        (21.2514, 81.6296), (21.2300, 81.5800), (21.2100, 81.5200),
        (21.1900, 81.4800), (21.1800, 81.4200), (21.1600, 81.3800),
        (21.1500, 81.3400), (21.1750, 81.2850), (21.1950, 81.2300),
    ],
    "NH-43": [
        (21.2514, 81.6296), (21.3200, 81.7000), (21.4000, 81.7800),
        (21.5000, 81.8200), (21.6000, 81.8800), (21.7200, 81.9200),
        (21.8500, 81.9600), (21.9500, 82.0200), (22.0796, 82.1391),
    ],
    "NH-130": [
        (21.2514, 81.6296), (21.1500, 81.6800), (21.0200, 81.7200),
        (20.9000, 81.7800), (20.7500, 81.8200), (20.5500, 81.9000),
        (20.2600, 81.9600), (19.9500, 82.0200), (19.0860, 82.0210),
    ],
    "NH-49": [
        (21.2514, 81.6296), (21.1800, 81.5600), (21.0800, 81.4800),
        (20.9500, 81.4200), (20.8200, 81.3600), (20.7000, 81.2800),
        (20.5500, 81.1800), (20.3500, 81.0600),
    ],
    "NH-353": [
        (23.1185, 83.1986), (23.0500, 83.3200), (22.9800, 83.4800),
        (22.9000, 83.6200), (22.8000, 83.7800), (22.6500, 83.8800),
        (22.4800, 83.9500), (22.1000, 83.3967),
    ],
}

SOURCES = ["Sentinel-2", "CARTOSAT-3", "Landsat-9", "EOS-04", "Drone/OAM", "CCTV", "Mobile", "Mapillary"]
SEVERITIES = ["Critical", "High", "Medium", "Low"]
SEV_WEIGHTS = [0.1, 0.25, 0.4, 0.25]
COMPLAINT_STATUSES = ["DETECTED", "FILED", "ACKNOWLEDGED", "IN_PROGRESS", "REPAIRED"]
TASK_NAMES = [
    "app.tasks.satellite.ingest_all_sources", "app.tasks.inference.run_yolo_batch",
    "app.tasks.filing.generate_and_file_complaint", "app.tasks.weather.fetch_all_weather",
    "app.tasks.verification.scan_repairs", "app.tasks.data_sources.refresh_all",
    "app.tasks.cctv.capture_all_frames", "app.tasks.escalation.daily_escalation_check",
]

SATELLITE_SOURCES = [
    ("sentinel_2", "Sentinel-2 (ESA)", "optical", 10, 5, True),
    ("sentinel_1", "Sentinel-1 SAR (ESA)", "sar", 5, 12, True),
    ("cartosat_3", "CARTOSAT-3 (ISRO)", "optical", 0.25, 5, False),
    ("cartosat_2s", "CARTOSAT-2S (ISRO)", "optical", 0.6, 25, False),
    ("resourcesat_2a", "ResourceSat-2A LISS-IV (ISRO)", "optical", 5, 24, True),
    ("eos04_risat", "EOS-04/RISAT-1A (ISRO)", "sar", 1, 22, True),
    ("landsat_9", "Landsat-9 (USGS/NASA)", "optical", 30, 16, True),
    ("alos2_palsar", "ALOS-2 PALSAR-2 (JAXA)", "sar", 3, 14, False),
    ("modis_viirs", "MODIS+VIIRS Thermal (NASA)", "thermal", 250, 1, True),
]

now = datetime.now(timezone.utc)

def rand_delta(max_days=90):
    return timedelta(days=random.randint(1, max_days), hours=random.randint(0, 23), minutes=random.randint(0, 59))


async def seed():
    """Seed all tables with realistic demo data."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # ── Check if already seeded ──────────────────────────────
        existing = (await db.execute(select(Pothole))).scalars().first()
        if existing:
            print("⚠  Database already seeded. Skipping.")
            return

        print("🌱 Seeding database...")

        # ── 1. Admin User ────────────────────────────────────────
        admin_exists = (await db.execute(
            select(AdminUser).where(AdminUser.email == settings.ADMIN_DEFAULT_EMAIL)
        )).scalar_one_or_none()
        if not admin_exists:
            db.add(AdminUser(
                email=settings.ADMIN_DEFAULT_EMAIL, name="System Admin",
                role="SUPER_ADMIN", password_hash=hash_password(settings.ADMIN_DEFAULT_PASSWORD),
                status="ACTIVE",
            ))
            await db.flush()
        print("  ✓ Admin user")

        # ── 2. Satellite Sources ─────────────────────────────────
        for sname, dname, stype, res, cycle, creds in SATELLITE_SOURCES:
            db.add(SatelliteSource(
                source_name=sname, display_name=dname, source_type=stype,
                resolution_m=res, repeat_cycle_days=cycle, status="ACTIVE" if creds else "INACTIVE",
                credentials_configured=creds,
                last_successful_download=now - rand_delta(14) if creds else None,
                last_attempt=now - rand_delta(3),
                config={"api_endpoint": f"https://api.example.com/{sname}", "max_cloud_cover": 30},
            ))
        print("  ✓ 9 satellite sources")

        # ── 3. CCTV Cameras ──────────────────────────────────────
        cctv_data = [
            ("CG-CAM-001", 21.2514, 81.6296, "NH-30", 0, "ATMS-Zone-Raipur"),
            ("CG-CAM-002", 21.1800, 81.4200, "NH-30", 32, "ATMS-Zone-Durg"),
            ("CG-CAM-003", 22.0796, 82.1391, "NH-43", 280, "ATMS-Zone-Bilaspur"),
            ("CG-CAM-004", 20.2600, 81.9600, "NH-130", 180, "ATMS-Zone-Kondagaon"),
            ("CG-CAM-005", 23.1185, 83.1986, "NH-353", 0, "ATMS-Zone-Ambikapur"),
        ]
        for cam_id, lat, lon, hw, km, zone in cctv_data:
            db.add(CCTVNode(
                camera_id=cam_id, geom=f"SRID=4326;POINT({lon} {lat})",
                highway=hw, km_marker=km, rtsp_url=f"rtsp://nhai-cctv.gov.in/{cam_id}/stream1",
                atms_zone=zone, mounting_height_m=8, camera_angle_degrees=15,
                status="ACTIVE", last_active=now - timedelta(minutes=random.randint(1, 30)),
            ))
        print("  ✓ 5 CCTV cameras")

        # ── 4. Drone Missions ────────────────────────────────────
        drone_data = [
            ("Survey NH-30 KM 0-50", "DJI Matrice 350 RTK", "NH-30", 0, 50, "COMPLETED", 342, 2.5),
            ("Monsoon Damage NH-43", "DJI Phantom 4 RTK", "NH-43", 100, 175, "COMPLETED", 518, 3.8),
            ("NH-130 Bridge Scan", "OpenAerialMap", "NH-130", 80, 95, "PROCESSING", 156, 0.8),
        ]
        for mname, src, hw, kms, kme, status, imgs, area in drone_data:
            db.add(DroneMission(
                mission_name=mname, source=src, operator="CG Road Survey Team",
                mission_date=date.today() - timedelta(days=random.randint(3, 30)),
                highway=hw, km_start=kms, km_end=kme,
                area_covered_sqkm=area, image_count=imgs, resolution_cm_px=Decimal("2.5"),
                processing_status=status, detection_count=random.randint(8, 45),
                submitted_at=now - rand_delta(30),
                completed_at=now - rand_delta(5) if status == "COMPLETED" else None,
            ))
        print("  ✓ 3 drone missions")

        # ── 5. Model Registry ────────────────────────────────────
        models = [
            ("YOLOv8x-seg", "1.0.0", 0.891, 0.756, 0.032, 15200, True),
            ("YOLOv8x-seg", "0.9.2", 0.867, 0.722, 0.048, 12800, False),
            ("MiDaS-v3-DPT-Large", "1.0.0", None, None, None, None, True),
            ("Siamese-RepairNet", "1.0.0", 0.923, 0.891, 0.021, 4200, True),
        ]
        for mtype, ver, map50, map75, fpr, imgs, active in models:
            db.add(ModelRegistry(
                model_type=mtype, version=ver, val_map50=map50, val_map75=map75,
                false_positive_rate=fpr, training_images=imgs, active=active,
                trained_at=now - rand_delta(60),
                model_path=f"models/{mtype.lower()}-v{ver}.pt",
            ))
        print("  ✓ 4 model registry entries")

        # ── 6. System Settings ───────────────────────────────────
        settings_data = [
            ("confidence_threshold_auto_file", "0.85", "float", "Confidence above which complaints auto-file"),
            ("confidence_threshold_review", "0.65", "float", "Confidence below which detections need review"),
            ("jolt_threshold_kmh", "3.5", "float", "Minimum jolt magnitude for pothole registration"),
            ("cluster_radius_m", "15", "int", "Radius for clustering nearby reports"),
            ("escalation_tier1_hours", "72", "int", "Hours before Tier 1 escalation"),
            ("escalation_tier2_hours", "168", "int", "Hours before Tier 2 escalation"),
            ("escalation_tier3_hours", "336", "int", "Hours before Tier 3 escalation"),
            ("max_inference_batch_size", "32", "int", "Max images per inference batch"),
            ("weather_risk_multiplier", "1.5", "float", "Risk score multiplier during rain"),
            ("sar_fallback_enabled", "true", "bool", "Use SAR satellites during cloudy conditions"),
            ("gemini_model", "gemini-1.5-flash", "string", "Gemini model for complaint generation"),
            ("repair_ssim_threshold", "0.80", "float", "SSIM score indicating repair"),
        ]
        for key, val, vtype, desc in settings_data:
            db.add(SystemSetting(
                key=key, value=val, value_type=vtype, description=desc,
                last_modified=now - rand_delta(30),
            ))
        print("  ✓ 12 system settings")

        # ── 7. Potholes (100+) ───────────────────────────────────
        pothole_ids = []
        for highway, coords in NH_ROUTES.items():
            for i in range(20):
                idx = random.randint(0, len(coords) - 2)
                lat1, lon1 = coords[idx]
                lat2, lon2 = coords[idx + 1]
                t = random.random()
                lat = lat1 + t * (lat2 - lat1) + random.uniform(-0.005, 0.005)
                lon = lon1 + t * (lon2 - lon1) + random.uniform(-0.005, 0.005)

                severity = random.choices(SEVERITIES, weights=SEV_WEIGHTS)[0]
                source = random.choice(SOURCES)
                area = round(random.uniform(0.1, 3.5), 2) if severity != "Low" else round(random.uniform(0.05, 0.5), 2)
                depth = round(random.uniform(2, 18), 1) if severity in ("Critical", "High") else round(random.uniform(1, 6), 1)
                confidence = round(random.uniform(0.7, 0.99), 3) if severity != "Low" else round(random.uniform(0.55, 0.85), 3)
                risk = round(random.uniform(7, 10), 1) if severity == "Critical" else (
                    round(random.uniform(5, 8), 1) if severity == "High" else round(random.uniform(2, 6), 1)
                )
                km = round(random.uniform(0, 300), 1)
                detected_at = now - rand_delta(60)

                p = Pothole(
                    geom=f"SRID=4326;POINT({lon} {lat})",
                    severity=severity, area_sqm=area, depth_cm=depth,
                    risk_score=risk, confidence_score=confidence,
                    source_primary=source, road_name=highway,
                    km_marker=km,
                    district=random.choice(["Raipur", "Durg", "Bilaspur", "Jagdalpur", "Ambikapur", "Raigarh", "Korba", "Kanker"]),
                    state="Chhattisgarh", rain_flag=random.random() < 0.3,
                    critically_overdue=severity == "Critical" and random.random() < 0.2,
                    detected_at=detected_at,
                    image_path=f"satellite/{source.lower()}/detection_{random.randint(10000,99999)}.tif",
                    base_risk_score=risk - random.uniform(0, 1.5),
                    detection_metadata={"model": "yolov8x-seg", "batch_id": random.randint(100, 999)},
                )
                db.add(p)
                await db.flush()
                pothole_ids.append((p.id, severity, detected_at, highway, km, risk))

        print(f"  ✓ {len(pothole_ids)} potholes across 5 highways")

        # ── 8. Complaints ────────────────────────────────────────
        complaint_count = 0
        for pid, sev, det_at, hw, km, risk in pothole_ids:
            if random.random() < 0.6:
                status = random.choices(COMPLAINT_STATUSES, weights=[0.1, 0.25, 0.25, 0.2, 0.2])[0]
                escalation = 0 if status in ("DETECTED", "FILED") else random.randint(0, 2)
                filed_at = det_at + timedelta(hours=random.randint(1, 48))
                db.add(Complaint(
                    pothole_id=pid,
                    complaint_text=f"Severe {sev.lower()} pothole at KM {km} on {hw}. Area: ~{random.uniform(0.2, 3):.1f} m². Depth: ~{random.uniform(2, 15):.0f} cm. Immediate repair required.",
                    status=status, escalation_level=escalation,
                    portal_ref=f"CG/NHAI/{random.randint(2024, 2026)}/{random.randint(10000, 99999)}" if status != "DETECTED" else None,
                    filed_at=filed_at if status != "DETECTED" else None,
                    escalated_at=filed_at + timedelta(days=3) if escalation > 0 else None,
                    rain_flag=random.random() < 0.35,
                    gemini_model="gemini-1.5-flash",
                    filing_source="PG_PORTAL",
                ))
                complaint_count += 1
        print(f"  ✓ {complaint_count} complaints")

        # ── 9. Source Reports ────────────────────────────────────
        for pid, sev, det_at, hw, km, risk in random.sample(pothole_ids, min(30, len(pothole_ids))):
            db.add(SourceReport(
                pothole_id=pid, source="mobile_crowdsource",
                report_type="VISUAL" if random.random() < 0.6 else "VIBRATION",
                jolt_magnitude=round(random.uniform(3.5, 12.0), 2),
                timestamp=det_at + timedelta(hours=random.randint(0, 72)),
                confidence_boost=round(random.uniform(0.02, 0.08), 3),
            ))
        print("  ✓ 30 source reports")

        # ── 10. Task History ─────────────────────────────────────
        for i in range(50):
            started = now - rand_delta(14)
            duration = round(random.uniform(1.5, 120.0), 1)
            status = random.choices(["SUCCESS", "FAILURE", "RETRY"], weights=[0.85, 0.1, 0.05])[0]
            db.add(TaskHistory(
                task_name=random.choice(TASK_NAMES),
                queue=random.choice(["satellite_queue", "inference_queue", "filing_queue", "default"]),
                status=status, started_at=started,
                completed_at=started + timedelta(seconds=duration),
                duration_seconds=duration,
                error_message="Connection timeout to external API" if status == "FAILURE" else None,
            ))
        print("  ✓ 50 task history entries")

        # ── 11. Gemini Audit Logs ────────────────────────────────
        for pid, sev, det_at, hw, km, risk in random.sample(pothole_ids, min(20, len(pothole_ids))):
            db.add(GeminiAudit(
                pothole_id=pid, use_case="complaint_generation",
                prompt_text=f"Generate formal complaint for {sev} pothole at KM {km}...",
                response_text=f"Subject: Urgent Pothole Repair — {hw} KM {km}\n\nDear Sir/Madam...",
                model_name="gemini-1.5-flash", prompt_tokens=random.randint(200, 500),
                completion_tokens=random.randint(400, 800),
                called_at=det_at + timedelta(hours=random.randint(1, 24)),
                success=True,
            ))
        print("  ✓ 20 Gemini audit logs")

        # ── 12. Admin Audit Logs ─────────────────────────────────
        actions = ["LOGIN", "UPDATE_SATELLITE_SOURCE", "ACCEPT_DETECTION", "REJECT_DETECTION",
                   "TRIGGER_SATELLITE_INGESTION", "UPDATE_SETTING", "PROMOTE_MODEL"]
        for i in range(25):
            db.add(AdminAuditLog(
                administrator_id=1, action_type=random.choice(actions),
                resource_type=random.choice(["satellite_sources", "potholes", "system_settings", "model_registry"]),
                resource_id=str(random.randint(1, 50)),
                change_summary=f"Admin action #{i+1}",
                performed_at=now - rand_delta(30),
            ))
        print("  ✓ 25 admin audit logs")

        # ── 13. Satellite Download Logs ──────────────────────────
        for i in range(15):
            src = random.choice(["sentinel_2", "sentinel_1", "landsat_9", "cartosat_3"])
            started = now - rand_delta(30)
            db.add(SatelliteDownloadLog(
                source=src, product_id=f"{src.upper()}-{random.randint(100000, 999999)}",
                highway=random.choice(list(NH_ROUTES.keys())),
                download_started_at=started,
                download_completed_at=started + timedelta(minutes=random.randint(2, 45)),
                file_size_mb=round(random.uniform(50, 800), 1),
                cloud_cover_pct=round(random.uniform(0, 35), 1),
                success=random.random() < 0.85,
                error_message=None if random.random() < 0.85 else "Timeout during download",
            ))
        print("  ✓ 15 satellite download logs")

        # ── 14. Selection Logs ───────────────────────────────────
        for i in range(10):
            db.add(SatelliteSelectionLog(
                highway=random.choice(list(NH_ROUTES.keys())),
                selected_source=random.choice(["sentinel_2", "cartosat_3", "landsat_9"]),
                reason=random.choice(["Best resolution available", "Cloud-free window", "SAR fallback due to monsoon", "Scheduled cycle priority"]),
                considered_sources=["sentinel_2", "cartosat_3", "landsat_9", "sentinel_1"],
                detection_cycle_date=date.today() - timedelta(days=random.randint(0, 30)),
                selected_at=now - rand_delta(14),
            ))
        print("  ✓ 10 selection logs")

        await db.commit()
        print(f"\n🎉 Seeding complete! {len(pothole_ids)} potholes, {complaint_count} complaints, and all supporting data.")


if __name__ == "__main__":
    asyncio.run(seed())
