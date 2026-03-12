"""Inference Celery tasks — YOLOv8, MiDaS, classification."""

from __future__ import annotations

from app.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("tasks.inference")


@celery_app.task(name="app.tasks.inference.process_satellite_tiles", bind=True, max_retries=2)
def process_satellite_tiles(self, job_id: int) -> dict:
    """Run YOLOv8 inference on satellite tiles from a completed download job."""
    logger.info("process_satellite_tiles", job_id=job_id)
    try:
        from app.services.detection.pipeline import DetectionPipeline
        pipeline = DetectionPipeline()
        return pipeline.process_satellite_job(job_id)
    except Exception as exc:
        logger.error("satellite_inference_failed", job_id=job_id, error=str(exc))
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.inference.process_drone_orthophoto", bind=True, max_retries=2)
def process_drone_orthophoto(self, mission_id: int) -> dict:
    """Run YOLOv8 inference on a processed drone orthophoto."""
    logger.info("process_drone_orthophoto", mission_id=mission_id)
    try:
        from app.services.detection.pipeline import DetectionPipeline
        pipeline = DetectionPipeline()
        return pipeline.process_drone_mission(mission_id)
    except Exception as exc:
        logger.error("drone_inference_failed", mission_id=mission_id, error=str(exc))
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.inference.process_cctv_frame")
def process_cctv_frame(camera_id: str, frame_path: str, timestamp: str) -> dict:
    """Run YOLOv8 inference on a single CCTV frame."""
    logger.info("process_cctv_frame", camera_id=camera_id)
    from app.services.detection.pipeline import DetectionPipeline
    pipeline = DetectionPipeline()
    return pipeline.process_cctv_frame(camera_id, frame_path, timestamp)


@celery_app.task(name="app.tasks.inference.process_mobile_report", bind=True, max_retries=2)
def process_mobile_report(self, report_id: int) -> dict:
    """Run YOLOv8 inference on a mobile visual report video."""
    logger.info("process_mobile_report", report_id=report_id)
    try:
        from app.services.detection.pipeline import DetectionPipeline
        pipeline = DetectionPipeline()
        return pipeline.process_mobile_report(report_id)
    except Exception as exc:
        logger.error("mobile_inference_failed", report_id=report_id, error=str(exc))
        self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.tasks.inference.run_depth_estimation")
def run_depth_estimation(pothole_id: int, image_path: str) -> dict:
    """Run MiDaS depth estimation on a detected pothole crop."""
    logger.info("run_depth_estimation", pothole_id=pothole_id)
    from app.services.detection.depth import DepthEstimator
    estimator = DepthEstimator()
    return estimator.estimate(pothole_id, image_path)
