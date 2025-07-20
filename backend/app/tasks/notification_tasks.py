"""
Notification Tasks
Celery tasks for sending notifications and alerts
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from celery import Task
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


class NotificationTask(Task):
    """Base task class for notification operations"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Notification task {task_id} failed: {exc}")


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="app.tasks.notification_tasks.send_notification"
)
def send_notification(
    self,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    channels: List[str] = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Send notification to user through specified channels"""
    try:
        if channels is None:
            channels = ['in_app']
        if metadata is None:
            metadata = {}
            
        logger.info(f"Sending {notification_type} notification to user {user_id}")
        
        # Mock notification sending
        delivery_results = []
        
        for channel in channels:
            try:
                # Simulate different delivery methods
                if channel == 'email':
                    # Mock email delivery
                    delivery_results.append({
                        'channel': 'email',
                        'status': 'delivered',
                        'delivery_id': f"email_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'delivery_time_ms': 234
                    })
                elif channel == 'sms':
                    # Mock SMS delivery
                    delivery_results.append({
                        'channel': 'sms',
                        'status': 'delivered',
                        'delivery_id': f"sms_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'delivery_time_ms': 567
                    })
                elif channel == 'slack':
                    # Mock Slack delivery
                    delivery_results.append({
                        'channel': 'slack',
                        'status': 'delivered',
                        'delivery_id': f"slack_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'delivery_time_ms': 123
                    })
                else:  # in_app
                    # Mock in-app notification
                    delivery_results.append({
                        'channel': 'in_app',
                        'status': 'delivered',
                        'delivery_id': f"app_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'delivery_time_ms': 45
                    })
                    
            except Exception as channel_exc:
                logger.error(f"Failed to deliver notification via {channel}: {channel_exc}")
                delivery_results.append({
                    'channel': channel,
                    'status': 'failed',
                    'error': str(channel_exc)
                })
        
        notification_result = {
            'user_id': user_id,
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'channels_attempted': channels,
            'delivery_results': delivery_results,
            'successful_deliveries': len([r for r in delivery_results if r['status'] == 'delivered']),
            'failed_deliveries': len([r for r in delivery_results if r['status'] == 'failed']),
            'sent_at': datetime.now(timezone.utc).isoformat(),
            'task_id': self.request.id
        }
        
        return notification_result
        
    except Exception as exc:
        logger.error(f"Notification sending failed for user {user_id}: {exc}")
        raise


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="app.tasks.notification_tasks.send_daily_brief_notification"
)
def send_daily_brief_notification(
    self,
    user_id: str,
    brief_summary: str,
    brief_url: str
) -> Dict[str, Any]:
    """Send daily brief notification to user"""
    try:
        logger.info(f"Sending daily brief notification to user {user_id}")
        
        title = "Your Daily Intelligence Brief is Ready"
        message = f"Your personalized brief is ready: {brief_summary[:100]}..."
        
        # Determine notification channels based on user preferences
        # Mock user preferences lookup
        user_channels = ['in_app', 'email']  # Would come from user preferences
        
        return send_notification.apply(
            args=[
                user_id,
                'daily_brief',
                title,
                message,
                user_channels,
                {
                    'brief_url': brief_url,
                    'brief_type': 'daily',
                    'auto_generated': True
                }
            ],
            task_id=self.request.id
        ).get()
        
    except Exception as exc:
        logger.error(f"Daily brief notification failed for user {user_id}: {exc}")
        raise


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="app.tasks.notification_tasks.send_alert"
)
def send_alert(
    self,
    organization_id: str,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    affected_users: List[str] = None
) -> Dict[str, Any]:
    """Send alert notifications to affected users"""
    try:
        if affected_users is None:
            # If no specific users, send to all org admins
            affected_users = ['admin_user_1', 'admin_user_2']  # Mock admin lookup
            
        logger.info(f"Sending {severity} alert to {len(affected_users)} users in org {organization_id}")
        
        # Determine channels based on severity
        if severity == 'critical':
            channels = ['in_app', 'email', 'sms']
        elif severity == 'high':
            channels = ['in_app', 'email']
        else:
            channels = ['in_app']
        
        alert_results = []
        
        for user_id in affected_users:
            try:
                result = send_notification.apply(
                    args=[
                        user_id,
                        f'alert_{alert_type}',
                        f"🚨 {title}",
                        message,
                        channels,
                        {
                            'organization_id': organization_id,
                            'alert_type': alert_type,
                            'severity': severity,
                            'requires_action': severity in ['critical', 'high']
                        }
                    ]
                ).get()
                
                alert_results.append({
                    'user_id': user_id,
                    'status': 'sent',
                    'deliveries': result['successful_deliveries']
                })
                
            except Exception as user_exc:
                logger.error(f"Failed to send alert to user {user_id}: {user_exc}")
                alert_results.append({
                    'user_id': user_id,
                    'status': 'failed',
                    'error': str(user_exc)
                })
        
        return {
            'organization_id': organization_id,
            'alert_type': alert_type,
            'severity': severity,
            'title': title,
            'users_notified': len([r for r in alert_results if r['status'] == 'sent']),
            'notification_failures': len([r for r in alert_results if r['status'] == 'failed']),
            'alert_results': alert_results,
            'sent_at': datetime.now(timezone.utc).isoformat(),
            'task_id': self.request.id
        }
        
    except Exception as exc:
        logger.error(f"Alert sending failed for org {organization_id}: {exc}")
        raise


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="app.tasks.notification_tasks.send_integration_status"
)
def send_integration_status(
    self,
    organization_id: str,
    integration_name: str,
    status: str,
    details: str
) -> Dict[str, Any]:
    """Send integration status notifications"""
    try:
        logger.info(f"Sending integration status notification for {integration_name} in org {organization_id}")
        
        # Determine if notification is needed based on status
        if status in ['error', 'warning']:
            severity = 'high' if status == 'error' else 'medium'
            
            title = f"Integration Issue: {integration_name}"
            message = f"Your {integration_name} integration status is {status}. {details}"
            
            # Send to admin users
            admin_users = ['admin_user_1']  # Mock admin lookup
            
            return send_alert.apply(
                args=[
                    organization_id,
                    'integration_issue',
                    severity,
                    title,
                    message,
                    admin_users
                ],
                task_id=self.request.id
            ).get()
        
        else:
            # Status is healthy, no notification needed
            return {
                'organization_id': organization_id,
                'integration_name': integration_name,
                'status': status,
                'notification_sent': False,
                'reason': 'Status is healthy, no notification required',
                'checked_at': datetime.now(timezone.utc).isoformat(),
                'task_id': self.request.id
            }
            
    except Exception as exc:
        logger.error(f"Integration status notification failed: {exc}")
        raise


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="app.tasks.notification_tasks.send_batch_notifications"
)
def send_batch_notifications(
    self,
    notifications: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send multiple notifications in batch"""
    try:
        logger.info(f"Sending batch of {len(notifications)} notifications")
        
        batch_results = []
        
        for notification in notifications:
            try:
                result = send_notification.apply(
                    args=[
                        notification['user_id'],
                        notification['type'],
                        notification['title'],
                        notification['message'],
                        notification.get('channels', ['in_app']),
                        notification.get('metadata', {})
                    ]
                ).get()
                
                batch_results.append({
                    'user_id': notification['user_id'],
                    'status': 'sent',
                    'deliveries': result['successful_deliveries']
                })
                
            except Exception as notif_exc:
                logger.error(f"Failed to send notification in batch: {notif_exc}")
                batch_results.append({
                    'user_id': notification.get('user_id', 'unknown'),
                    'status': 'failed',
                    'error': str(notif_exc)
                })
        
        return {
            'batch_id': self.request.id,
            'total_notifications': len(notifications),
            'successful_sends': len([r for r in batch_results if r['status'] == 'sent']),
            'failed_sends': len([r for r in batch_results if r['status'] == 'failed']),
            'batch_results': batch_results,
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Batch notification sending failed: {exc}")
        raise


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="app.tasks.notification_tasks.cleanup_old_notifications"
)
def cleanup_old_notifications(
    self,
    days_old: int = 30
) -> Dict[str, Any]:
    """Clean up old notifications (periodic task)"""
    try:
        logger.info(f"Cleaning up notifications older than {days_old} days")
        
        # Mock cleanup process
        cleanup_result = {
            'cutoff_days': days_old,
            'notifications_deleted': 1847,
            'storage_freed_mb': 23.4,
            'cleanup_duration_seconds': 45,
            'cleaned_at': datetime.now(timezone.utc).isoformat(),
            'task_id': self.request.id
        }
        
        return cleanup_result
        
    except Exception as exc:
        logger.error(f"Notification cleanup failed: {exc}")
        raise