"""Risk score computation engine."""

from __future__ import annotations

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("services.risk")

SEVERITY_SCORES = {"Critical": 4.0, "High": 3.0, "Medium": 2.0, "Low": 1.0}
TRAFFIC_SCORES = {"High": 2.0, "Medium": 1.2, "Low": 0.5}


class RiskScoreEngine:
    """Compute risk score from 0.0 to 10.0 based on multiple factors."""

    def compute(
        self,
        severity: str,
        accident_count: int,
        traffic_volume: str,
        has_curves: bool,
        is_blind_spot: bool,
        slope_degrees: float = 0.0,
        junction_within_200m: bool = False,
        thermal_stress: bool = False,
        rain_imminent: bool = False,
        imd_warning_level: str | None = None,
        open_meteo_rain_mm: float = 0.0,
        gfs_rain_7d_mm: float = 0.0,
        eos04_moisture: bool = False,
        alos2_moisture: bool = False,
    ) -> dict:
        """Compute risk score and return breakdown."""

        # Severity component (35%)
        severity_raw = SEVERITY_SCORES.get(severity, 1.0)
        severity_component = severity_raw * settings.RISK_SEVERITY_WEIGHT * 10 / 4.0

        # Accident history component (30%)
        accident_raw = min(accident_count / 3.0, 4.0)
        accident_component = accident_raw * settings.RISK_ACCIDENT_WEIGHT * 10 / 4.0

        # Traffic volume component (20%)
        traffic_raw = TRAFFIC_SCORES.get(traffic_volume, 0.5)
        traffic_component = traffic_raw * settings.RISK_TRAFFIC_WEIGHT * 10 / 2.0

        # Road geometry component (15%)
        geometry_raw = 1.5 if (has_curves or is_blind_spot) else 0.0
        if slope_degrees > 5.0:
            geometry_raw += 0.3
        if junction_within_200m:
            geometry_raw += 0.2
        if thermal_stress:
            geometry_raw += 0.15
        geometry_component = geometry_raw * settings.RISK_GEOMETRY_WEIGHT * 10 / 2.15

        # Base risk score
        base_score = severity_component + accident_component + traffic_component + geometry_component
        base_score = min(base_score, 10.0)

        # Weather boost
        weather_boost = 1.0
        weather_reasons = []
        if imd_warning_level in ("Orange", "Red"):
            weather_boost = settings.RISK_WEATHER_BOOST
            weather_reasons.append(f"IMD {imd_warning_level} warning")
        if open_meteo_rain_mm > 10.0:
            weather_boost = max(weather_boost, settings.RISK_WEATHER_BOOST)
            weather_reasons.append(f"Open-Meteo {open_meteo_rain_mm}mm 48h")
        if gfs_rain_7d_mm > 50.0:
            weather_boost = max(weather_boost, settings.RISK_WEATHER_BOOST)
            weather_reasons.append(f"GFS {gfs_rain_7d_mm}mm 7-day")
        if eos04_moisture or alos2_moisture:
            weather_boost = max(weather_boost, settings.RISK_WEATHER_BOOST)
            weather_reasons.append("SAR moisture precursor")

        final_score = min(base_score * weather_boost, 10.0)

        # Urgency language
        if final_score >= 8.0:
            urgency = "EMERGENCY_IMMEDIATE"
        elif final_score >= 5.0:
            urgency = "URGENT_7_DAYS"
        else:
            urgency = "SCHEDULED_30_DAYS"

        result = {
            "risk_score": round(final_score, 2),
            "base_risk_score": round(base_score, 2),
            "urgency": urgency,
            "weather_boost": weather_boost,
            "weather_reasons": weather_reasons,
            "breakdown": {
                "severity": round(severity_component, 2),
                "accident": round(accident_component, 2),
                "traffic": round(traffic_component, 2),
                "geometry": round(geometry_component, 2),
            },
        }

        logger.info("risk_score_computed", **result)
        return result
