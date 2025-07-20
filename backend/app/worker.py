"""
Celery Worker Startup Script
Entry point for running Celery workers
"""

import logging

from app.tasks.celery_app import celery_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting SingleBrief Celery Worker...")

    # Configure worker
    celery_app.start(
        argv=[
            "worker",
            "--loglevel=info",
            "--queues=intelligence,integrations,memory,notifications",
            "--concurrency=4",
            "--max-tasks-per-child=1000",
        ]
    )
