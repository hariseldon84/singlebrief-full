"""
Celery Application Configuration for SingleBrief
Handles asynchronous task processing for intelligence operations
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

# Create Celery instance
celery_app = Celery(
    "singlebrief",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.intelligence_tasks",
        "app.tasks.integration_tasks",
        "app.tasks.memory_tasks",
        "app.tasks.notification_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.intelligence_tasks.*": {"queue": "intelligence"},
        "app.tasks.integration_tasks.*": {"queue": "integrations"},
        "app.tasks.memory_tasks.*": {"queue": "memory"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task retries and timeouts
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_policy": {"timeout": 5.0},
    },
    # Worker settings
    worker_prefetch_multiplier=1,  # Disable prefetching for better load distribution
    worker_max_tasks_per_child=1000,  # Restart workers after 1000 tasks
    # Task prioritization
    task_default_priority=5,
    worker_disable_rate_limits=False,
    task_annotations={
        "app.tasks.intelligence_tasks.process_urgent_query": {"priority": 9},
        "app.tasks.intelligence_tasks.process_daily_brief": {"priority": 7},
        "app.tasks.intelligence_tasks.process_regular_query": {"priority": 5},
        "app.tasks.integration_tasks.sync_integration_data": {"priority": 3},
        "app.tasks.memory_tasks.update_memory": {"priority": 2},
        "app.tasks.notification_tasks.send_notification": {"priority": 1},
    },
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

# Optional: Configure beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Daily intelligence gathering
    "daily-intelligence-gathering": {
        "task": "app.tasks.intelligence_tasks.generate_daily_briefs",
        "schedule": 300.0,  # Every 5 minutes for demo (change to crontab for production)
        "options": {"priority": 7},
    },
    # Sync integration data
    "sync-integration-data": {
        "task": "app.tasks.integration_tasks.sync_all_integrations",
        "schedule": 900.0,  # Every 15 minutes
        "options": {"priority": 3},
    },
    # Memory consolidation
    "memory-consolidation": {
        "task": "app.tasks.memory_tasks.consolidate_memories",
        "schedule": 3600.0,  # Every hour
        "options": {"priority": 2},
    },
    # Health checks
    "system-health-check": {
        "task": "app.tasks.intelligence_tasks.health_check_all_modules",
        "schedule": 600.0,  # Every 10 minutes
        "options": {"priority": 1},
    },
}
