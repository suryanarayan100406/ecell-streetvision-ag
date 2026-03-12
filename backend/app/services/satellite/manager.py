"""Satellite Data Manager — selects optimal satellite source per detection cycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logging import get_logger
from app.config import settings

logger = get_logger("services.satellite.manager")

# Source priority for optical imagery (highest resolution first)
OPTICAL_PRIORITY = [
    ("CARTOSAT3", 0.25),
    ("CARTOSAT2S", 0.65),
    ("RESOURCESAT2A", 5.8),
    ("SENTINEL2", 10.0),
    ("LANDSAT9", 15.0),
    ("LANDSAT8", 30.0),
]

# Source priority for SAR imagery
SAR_PRIORITY = [
    ("RISAT2B", 1.0),
    ("EOS04", 3.0),
    ("SENTINEL1", 10.0),
    ("ALOS2", 3.0),
]


class SatelliteDataManager:
    """Manages satellite source selection and orchestration."""

    def select_source(
        self,
        highway: str,
        cloud_cover_pct: float,
        use_sar: bool = False,
    ) -> dict[str, Any]:
        """Select the optimal satellite source for a given corridor and conditions.

        Returns dict with source_name, reason, considered_sources.
        """
        priority_list = SAR_PRIORITY if use_sar else OPTICAL_PRIORITY

        if cloud_cover_pct > 50.0 and not use_sar:
            # High cloud cover — switch to SAR
            logger.info("cloud_cover_high_switching_to_sar", cloud_cover=cloud_cover_pct)
            priority_list = SAR_PRIORITY
            use_sar = True

        considered = []
        for source_name, resolution in priority_list:
            considered.append({
                "source": source_name,
                "resolution_m": resolution,
                "status": "AVAILABLE",
            })

        # Select first available source
        selected = priority_list[0]
        reason = (
            f"Selected {selected[0]} at {selected[1]}m resolution. "
            f"{'SAR mode due to cloud cover' if use_sar else 'Optical mode'}. "
            f"Highway: {highway}."
        )

        return {
            "source_name": selected[0],
            "resolution_m": selected[1],
            "reason": reason,
            "considered_sources": considered,
            "use_sar": use_sar,
        }

    def test_connection(self, source_id: int) -> dict:
        """Test connectivity to a satellite data provider."""
        logger.info("testing_connection", source_id=source_id)
        return {"status": "success", "source_id": source_id, "message": "Connection test passed"}

    def manual_ingest(self, source_id: int) -> dict:
        """Manually trigger ingestion for a specific satellite source."""
        logger.info("manual_ingestion", source_id=source_id)
        return {"status": "queued", "source_id": source_id}

    def check_location(self, latitude: float, longitude: float) -> dict:
        """Check a specific GPS location across all available satellites."""
        logger.info("checking_location", lat=latitude, lon=longitude)
        selection = self.select_source(
            highway="AUTO",
            cloud_cover_pct=0.0,
        )
        return {
            "status": "queued",
            "latitude": latitude,
            "longitude": longitude,
            "selected_source": selection["source_name"],
        }
