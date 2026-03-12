"""Confidence fusion engine — multiplicative multi-source confidence scoring."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.utils.logging import get_logger

logger = get_logger("services.detection.confidence")

# Source confidence multipliers
SOURCE_MULTIPLIERS: dict[str, float] = {
    "DRONE_HIGH_RES": 1.85,
    "CARTOSAT3": 1.8,
    "DRONE_MED_RES": 1.7,
    "CARTOSAT2S": 1.7,
    "OAM_DRONE": 1.7,
    "RISAT2B": 1.65,
    "CCTV": 1.6,
    "RESOURCESAT2A": 1.55,
    "MOBILE_VISUAL": 1.5,
    "DRONE_LOW_RES": 1.45,
    "MAPILLARY": 1.3,
    "KARTAVIEW": 1.3,
    "EOS04_MOISTURE": 1.25,
    "ALOS2_COHERENCE": 1.25,
    "MOBILE_CLUSTER": 1.2,
    "LANDSAT9_SWIR": 1.15,
    "SENTINEL1_SAR": 1.15,
    "MODIS_THERMAL": 1.1,
    "OSM_NOTE": 1.05,
}


class ConfidenceFusionEngine:
    """Computes fused confidence score from multiple independent sources."""

    def compute(
        self,
        base_confidence: float,
        corroborating_sources: list[str],
    ) -> float:
        """Compute multiplicative fused confidence.

        Args:
            base_confidence: YOLOv8 raw detection confidence (0.0-1.0).
            corroborating_sources: List of source keys from SOURCE_MULTIPLIERS.

        Returns:
            Fused confidence score capped at 1.0.
        """
        fused = base_confidence

        for source in corroborating_sources:
            multiplier = SOURCE_MULTIPLIERS.get(source, 1.0)
            fused *= multiplier
            logger.debug("applied_multiplier", source=source, multiplier=multiplier, fused=fused)

        # Cap at 1.0
        fused = min(fused, 1.0)

        logger.info(
            "confidence_computed",
            base=base_confidence,
            sources=len(corroborating_sources),
            fused=fused,
        )
        return round(fused, 3)

    def classify_action(self, confidence: float) -> str:
        """Classify the action based on confidence score thresholds."""
        from app.config import settings

        if confidence >= settings.AUTO_FILE_THRESHOLD:
            return "AUTO_FILE_COMPLAINT"
        elif confidence >= settings.REVIEW_THRESHOLD:
            return "FLAG_FOR_REVIEW"
        else:
            return "MONITOR"
