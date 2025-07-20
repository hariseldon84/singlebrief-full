"""
Intelligence Processing Tasks
Celery tasks for orchestrator and intelligence operations
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from celery import Task
from app.tasks.celery_app import celery_app
from app.orchestrator.core import OrchestratorAgent, QueryContext, QueryType
from app.orchestrator.modules import ModuleRegistry

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task class with callback support"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying due to: {exc}")


# Global orchestrator instance (will be initialized when worker starts)
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.intelligence_tasks.process_query",
    max_retries=3,
    default_retry_delay=60
)
def process_query(
    self,
    query: str,
    context_data: Dict[str, Any],
    priority: int = 5
) -> Dict[str, Any]:
    """
    Process an intelligence query asynchronously.
    
    Args:
        query: The user query to process
        context_data: Query context as dictionary
        priority: Task priority (1-10, higher = more urgent)
        
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Processing query task {self.request.id}: {query[:100]}...")
        
        # Create query context
        context = QueryContext(
            query_id=context_data.get('query_id', self.request.id),
            user_id=context_data.get('user_id', ''),
            organization_id=context_data.get('organization_id', ''),
            team_id=context_data.get('team_id'),
            session_id=context_data.get('session_id', ''),
            priority=priority,
            metadata=context_data.get('metadata', {})
        )
        
        # Process query using orchestrator
        orchestrator = get_orchestrator()
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                orchestrator.process_query(query, context)
            )
        finally:
            loop.close()
        
        # Convert result to dictionary for serialization
        return {
            'query_id': result.query_id,
            'status': result.status.value,
            'response': result.response,
            'confidence_score': result.confidence_score,
            'sources': result.sources,
            'processing_time_ms': result.processing_time_ms,
            'modules_used': result.modules_used,
            'error_message': result.error_message,
            'metadata': result.metadata,
            'task_id': self.request.id,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Query processing task failed: {exc}")
        
        # Retry for transient failures
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying query processing task (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        # Return error result
        return {
            'query_id': context_data.get('query_id', self.request.id),
            'status': 'failed',
            'response': None,
            'error_message': str(exc),
            'task_id': self.request.id,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.intelligence_tasks.process_urgent_query"
)
def process_urgent_query(
    self,
    query: str,
    context_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Process urgent queries with highest priority"""
    return process_query.apply(
        args=[query, context_data, 9],  # Priority 9 for urgent
        task_id=self.request.id
    ).get()


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.intelligence_tasks.process_regular_query"
)
def process_regular_query(
    self,
    query: str,
    context_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Process regular queries with normal priority"""
    return process_query.apply(
        args=[query, context_data, 5],  # Priority 5 for regular
        task_id=self.request.id
    ).get()


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.intelligence_tasks.process_daily_brief"
)
def process_daily_brief(
    self,
    user_id: str,
    organization_id: str,
    team_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate daily intelligence brief for a user"""
    try:
        logger.info(f"Generating daily brief for user {user_id}")
        
        # Create daily brief query
        query = "Generate my daily intelligence brief with team updates, project status, and key insights."
        
        context_data = {
            'query_id': f"daily_brief_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            'user_id': user_id,
            'organization_id': organization_id,
            'team_id': team_id,
            'metadata': {
                'query_type': 'daily_brief',
                'automated': True,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Process using regular query processor with high priority
        return process_query.apply(
            args=[query, context_data, 7],  # Priority 7 for daily briefs
            task_id=self.request.id
        ).get()
        
    except Exception as exc:
        logger.error(f"Daily brief generation failed for user {user_id}: {exc}")
        raise


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.intelligence_tasks.generate_daily_briefs"
)
def generate_daily_briefs(self) -> Dict[str, Any]:
    """Generate daily briefs for all active users (periodic task)"""
    try:
        logger.info("Starting daily brief generation for all users")
        
        # This would typically query the database for active users
        # For now, using mock data
        active_users = [
            {'user_id': 'user_1', 'organization_id': 'org_1', 'team_id': 'team_1'},
            {'user_id': 'user_2', 'organization_id': 'org_1', 'team_id': 'team_2'},
        ]
        
        generated_briefs = []
        
        for user in active_users:
            try:
                # Generate brief for each user
                brief_task = process_daily_brief.delay(
                    user_id=user['user_id'],
                    organization_id=user['organization_id'],
                    team_id=user['team_id']
                )
                
                generated_briefs.append({
                    'user_id': user['user_id'],
                    'task_id': brief_task.id,
                    'status': 'queued'
                })
                
            except Exception as user_exc:
                logger.error(f"Failed to queue daily brief for user {user['user_id']}: {user_exc}")
                generated_briefs.append({
                    'user_id': user['user_id'],
                    'status': 'failed',
                    'error': str(user_exc)
                })
        
        return {
            'total_users': len(active_users),
            'generated_briefs': generated_briefs,
            'generation_time': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Daily brief batch generation failed: {exc}")
        raise


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.intelligence_tasks.health_check_all_modules"
)
def health_check_all_modules(self) -> Dict[str, Any]:
    """Perform health check on all orchestrator modules"""
    try:
        logger.info("Performing health check on all modules")
        
        orchestrator = get_orchestrator()
        
        # Run async health check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            health_status = loop.run_until_complete(
                orchestrator.get_health_status()
            )
        finally:
            loop.close()
        
        return {
            'health_check_id': self.request.id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': health_status.get('orchestrator', 'unknown'),
            'module_status': health_status.get('modules', {}),
            'uptime_seconds': health_status.get('uptime_seconds', 0)
        }
        
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        return {
            'health_check_id': self.request.id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'unhealthy',
            'error': str(exc)
        }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.intelligence_tasks.batch_process_queries"
)
def batch_process_queries(
    self,
    queries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Process multiple queries in batch for efficiency"""
    try:
        logger.info(f"Processing batch of {len(queries)} queries")
        
        results = []
        
        for query_data in queries:
            try:
                # Extract query and context
                query = query_data['query']
                context_data = query_data['context']
                priority = query_data.get('priority', 5)
                
                # Process query
                result = process_query.apply(
                    args=[query, context_data, priority]
                ).get()
                
                results.append(result)
                
            except Exception as query_exc:
                logger.error(f"Failed to process query in batch: {query_exc}")
                results.append({
                    'query': query_data.get('query', 'unknown'),
                    'status': 'failed',
                    'error': str(query_exc)
                })
        
        return {
            'batch_id': self.request.id,
            'total_queries': len(queries),
            'processed': len(results),
            'results': results,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Batch processing failed: {exc}")
        raise


# Task status and monitoring utilities
@celery_app.task(name="app.tasks.intelligence_tasks.get_task_status")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a specific task"""
    try:
        result = celery_app.AsyncResult(task_id)
        
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None,
            'traceback': result.traceback if result.failed() else None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failed to get task status for {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'unknown',
            'error': str(exc)
        }