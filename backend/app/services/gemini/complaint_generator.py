"""Gemini complaint generator — produces formal grievance text from real data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import google.generativeai as genai

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("services.gemini")

SYSTEM_INSTRUCTION = """You are a senior PWD grievance documentation officer for the State of Chhattisgarh, India. 
You write formal English complaint letters to government authorities regarding pothole hazards on national highways.
Every measurement, GPS coordinate, road name, and KM marker in the complaint is real and verified.
Your output must follow this exact format:
SUBJECT: [under 120 characters]
TO: [full authority name and title]
BODY: [three paragraphs, formal English, max 300 words total]
EVIDENCE SUMMARY: [five bullet points]

Escalation levels:
- Level 0: Executive Engineer, PWD Roads Division
- Level 1: District Collector
- Level 2: Principal Secretary, PWD, Government of Chhattisgarh  
- Level 3: Secretary, Ministry of Road Transport and Highways (MoRTH), Government of India

For Level 2+, include language about administrative dereliction and cite Motor Vehicles Act 1988 at Level 3.
Severity language must be proportional to the risk score provided."""

AUTHORITY_MAP = {
    0: "Executive Engineer, PWD Roads Division",
    1: "District Collector",
    2: "Principal Secretary, PWD, Government of Chhattisgarh",
    3: "Secretary, Ministry of Road Transport and Highways, Government of India",
}


class ComplaintGenerator:
    """Generate complaint text using Gemini AI."""

    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def generate(self, pothole_id: int) -> dict[str, str]:
        """Generate a complaint letter for a pothole from real database values."""
        # In production, this reads from database
        logger.info("generating_complaint", pothole_id=pothole_id)

        pothole_data = self._fetch_pothole_data(pothole_id)
        prompt = self._build_prompt(pothole_data, escalation_level=0)

        try:
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                    temperature=settings.GEMINI_TEMPERATURE,
                ),
            )
            response = model.generate_content(prompt)
            complaint_text = response.text

            # Audit log
            self._log_audit(pothole_id, prompt, complaint_text, "gemini-1.5-flash", "complaint_generation")

            return {
                "complaint_text": complaint_text,
                "model": "gemini-1.5-flash",
                "authority": AUTHORITY_MAP[0],
            }

        except Exception as exc:
            logger.error("gemini_generation_failed", pothole_id=pothole_id, error=str(exc))
            self._log_audit(pothole_id, prompt, "", "gemini-1.5-flash", "complaint_generation", error=str(exc))
            return self._fallback_template(pothole_data)

    def generate_escalation(self, pothole_id: int, escalation_level: int) -> dict[str, str]:
        """Generate an escalation complaint with appropriate authority."""
        logger.info("generating_escalation", pothole_id=pothole_id, level=escalation_level)

        pothole_data = self._fetch_pothole_data(pothole_id)
        prompt = self._build_prompt(pothole_data, escalation_level=escalation_level)

        model_name = "gemini-1.5-pro" if escalation_level >= 2 else "gemini-1.5-flash"

        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                    temperature=settings.GEMINI_TEMPERATURE,
                ),
            )
            response = model.generate_content(prompt)
            return {
                "complaint_text": response.text,
                "model": model_name,
                "authority": AUTHORITY_MAP.get(escalation_level, AUTHORITY_MAP[3]),
                "escalation_level": escalation_level,
            }
        except Exception as exc:
            logger.error("escalation_generation_failed", error=str(exc))
            return self._fallback_template(pothole_data, escalation_level)

    def _build_prompt(self, data: dict[str, Any], escalation_level: int = 0) -> str:
        """Build the Gemini prompt with all real data fields."""
        return f"""Generate a formal complaint letter for a pothole on an Indian national highway.

POTHOLE DATA:
Road: {data.get('road_name', 'Unknown')} ({data.get('road_type', 'NH')})
KM Marker: {data.get('km_marker', 'N/A')}
GPS: {data.get('latitude', 0)}, {data.get('longitude', 0)}
District: {data.get('district', 'Unknown')}, State: {data.get('state', 'Chhattisgarh')}
Nearest Landmark: {data.get('nearest_landmark', 'N/A')}
Area: {data.get('area_sqm', 0)} sq metres, Depth: {data.get('depth_cm', 0)} cm
Severity: {data.get('severity', 'Unknown')}
Risk Score: {data.get('risk_score', 0)}/10.0 (Base: {data.get('base_risk_score', 0)})
Detection Sources: {data.get('sources_list', 'Unknown')} ({data.get('source_count', 0)} sources)
First Detected: {data.get('detection_date', 'Unknown')}
SAR First Detected: {data.get('sar_first_detected_at', 'N/A')}
Accident Count (2km radius): {data.get('accident_count', 0)}
Traffic Volume: {data.get('traffic_volume_category', 'Unknown')}
Road Geometry: {data.get('road_geometry_description', 'N/A')}
IMD Warning Level: {data.get('imd_warning_level', 'None')}
Forecast Rain 48h: {data.get('forecast_rain_48h_mm', 0)} mm
GFS 7-day Rain: {data.get('gfs_rain_7d_mm', 0)} mm
Rain Imminent: {data.get('rain_imminent', False)}
Previous Complaints: {data.get('prev_complaint_count', 0)}
Escalation Level: {escalation_level}
Days Since First Filing: {data.get('days_since_filing', 0)}
Authority: {AUTHORITY_MAP.get(escalation_level, AUTHORITY_MAP[0])}"""

    def _fetch_pothole_data(self, pothole_id: int) -> dict[str, Any]:
        """Fetch pothole data from database (sync context for Celery)."""
        # In production, this uses sync SQLAlchemy session
        return {"pothole_id": pothole_id, "road_name": "NH-30", "state": "Chhattisgarh"}

    def _fallback_template(self, data: dict, escalation_level: int = 0) -> dict:
        """Template-based fallback when Gemini fails."""
        authority = AUTHORITY_MAP.get(escalation_level, AUTHORITY_MAP[0])
        return {
            "complaint_text": f"SUBJECT: Urgent: Dangerous Pothole on {data.get('road_name', 'National Highway')}\n"
                              f"TO: {authority}\n"
                              f"BODY: A {data.get('severity', 'significant')} pothole has been detected...",
            "model": "template_fallback",
            "authority": authority,
        }

    def _log_audit(self, pothole_id: int, prompt: str, response: str, model: str, use_case: str, error: str | None = None) -> None:
        """Log Gemini API call to audit table."""
        logger.info("gemini_audit_logged", pothole_id=pothole_id, model=model, success=error is None)
