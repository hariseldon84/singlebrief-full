"""Multi-channel brief delivery service."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.brief import Brief, BriefDelivery, BriefFormat
from app.models.user import User

logger = logging.getLogger(__name__)

class DeliveryChannel(ABC):
    """Abstract base class for delivery channels."""

    @abstractmethod
    async def deliver(
        self, brief: Brief, recipient: str, format: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deliver brief through this channel."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate channel configuration."""
        pass

class EmailDeliveryChannel(DeliveryChannel):
    """Email delivery channel for briefs."""

    async def deliver(
        self, brief: Brief, recipient: str, format: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deliver brief via email."""
        try:
            # Email delivery implementation
            subject = config.get("subject", f"Daily Brief - {brief.title}")

            if format == "html":
                content = brief.content
                content_type = "text/html"
            else:
                # Convert HTML to plain text (simplified)
                content = self._html_to_text(brief.content or "")
                content_type = "text/plain"

            # Simulate email sending
            logger.info(f"Sending email to {recipient} with subject: {subject}")

            return {
                "status": "sent",
                "message_id": f"email_{brief.id}_{datetime.utcnow().timestamp()}",
                "sent_at": datetime.utcnow(),
                "recipient": recipient,
                "subject": subject,
            }

        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return {"status": "failed", "error": str(e), "failed_at": datetime.utcnow()}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate email configuration."""
        required_fields = ["recipient"]
        return all(field in config for field in required_fields)

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (simplified)."""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_content)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

class SlackDeliveryChannel(DeliveryChannel):
    """Slack delivery channel for briefs."""

    async def deliver(
        self, brief: Brief, recipient: str, format: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deliver brief via Slack."""
        try:
            channel = config.get("channel", recipient)
            webhook_url = config.get("webhook_url")

            # Format brief for Slack
            slack_content = self._format_for_slack(brief, config)

            # Simulate Slack message sending
            logger.info(f"Sending Slack message to {channel}")

            return {
                "status": "sent",
                "message_id": f"slack_{brief.id}_{datetime.utcnow().timestamp()}",
                "sent_at": datetime.utcnow(),
                "channel": channel,
            }

        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")
            return {"status": "failed", "error": str(e), "failed_at": datetime.utcnow()}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Slack configuration."""
        return "channel" in config or "webhook_url" in config

    def _format_for_slack(self, brief: Brief, config: Dict[str, Any]) -> Dict[str, Any]:
        """Format brief content for Slack."""
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": brief.title}},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": brief.summary or "Your daily brief is ready!",
                },
            },
        ]

        # Add action buttons
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Full Brief"},
                        "url": f"{settings.FRONTEND_URL}/briefs/{brief.id}",
                    }
                ],
            }
        )

        return {"blocks": blocks}

class DashboardDeliveryChannel(DeliveryChannel):
    """Dashboard/web delivery channel for briefs."""

    async def deliver(
        self, brief: Brief, recipient: str, format: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deliver brief to web dashboard."""
        try:
            # Dashboard delivery is immediate - brief is already available
            logger.info(f"Brief {brief.id} available on dashboard for user {recipient}")

            return {
                "status": "delivered",
                "delivered_at": datetime.utcnow(),
                "url": f"{settings.FRONTEND_URL}/briefs/{brief.id}",
                "recipient": recipient,
            }

        except Exception as e:
            logger.error(f"Dashboard delivery failed: {e}")
            return {"status": "failed", "error": str(e), "failed_at": datetime.utcnow()}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate dashboard configuration."""
        return True  # Dashboard delivery always available

class PDFDeliveryChannel(DeliveryChannel):
    """PDF generation and delivery channel."""

    async def deliver(
        self, brief: Brief, recipient: str, format: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate and deliver PDF version of brief."""
        try:
            # Generate PDF (placeholder implementation)
            pdf_content = self._generate_pdf(brief, config)
            pdf_filename = (
                f"brief_{brief.id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
            )

            # Store PDF (would save to cloud storage)
            pdf_url = f"{settings.FRONTEND_URL}/briefs/{brief.id}/download"

            logger.info(f"Generated PDF for brief {brief.id}")

            return {
                "status": "generated",
                "generated_at": datetime.utcnow(),
                "pdf_url": pdf_url,
                "filename": pdf_filename,
                "size_bytes": len(pdf_content),
            }

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return {"status": "failed", "error": str(e), "failed_at": datetime.utcnow()}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate PDF configuration."""
        return True

    def _generate_pdf(self, brief: Brief, config: Dict[str, Any]) -> bytes:
        """Generate PDF content (placeholder)."""
        # Would use a proper PDF library like WeasyPrint or ReportLab
        pdf_content = f"PDF content for brief: {brief.title}\n{brief.summary}"
        return pdf_content.encode("utf-8")

class BriefDeliveryService:
    """Service for managing multi-channel brief delivery."""

    def __init__(self, db: Session):
        self.db = db
        self.channels = {
            "email": EmailDeliveryChannel(),
            "slack": SlackDeliveryChannel(),
            "dashboard": DashboardDeliveryChannel(),
            "pdf": PDFDeliveryChannel(),
        }

    async def deliver_brief(
        self, brief_id: UUID, delivery_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deliver brief through multiple channels."""
        try:
            brief = self.db.query(Brief).filter(Brief.id == brief_id).first()
            if not brief:
                raise ValueError(f"Brief {brief_id} not found")

            delivery_results = []

            for config in delivery_configs:
                result = await self._deliver_single_channel(brief, config)
                delivery_results.append(result)

                # Store delivery record
                self._store_delivery_record(brief.id, config, result)

            return delivery_results

        except Exception as e:
            logger.error(f"Brief delivery failed: {e}")
            raise

    async def _deliver_single_channel(
        self, brief: Brief, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deliver brief through a single channel."""
        try:
            channel_name = config.get("channel")
            recipient = config.get("recipient")
            format = config.get("format", "html")
            channel_config = config.get("config", {})

            if channel_name not in self.channels:
                raise ValueError(f"Unknown delivery channel: {channel_name}")

            channel = self.channels[channel_name]

            # Validate configuration
            if not channel.validate_config({**channel_config, "recipient": recipient}):
                raise ValueError(f"Invalid configuration for {channel_name}")

            # Deliver through channel
            result = await channel.deliver(brief, recipient, format, channel_config)
            result["channel"] = channel_name
            result["brief_id"] = str(brief.id)

            return result

        except Exception as e:
            logger.error(f"Single channel delivery failed: {e}")
            return {
                "channel": config.get("channel"),
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow(),
            }

    def _store_delivery_record(
        self, brief_id: UUID, config: Dict[str, Any], result: Dict[str, Any]
    ):
        """Store delivery record in database."""
        try:
            delivery_record = BriefDelivery(
                brief_id=brief_id,
                channel=config.get("channel"),
                status=result.get("status"),
                format=config.get("format", "html"),
                recipient=config.get("recipient"),
                delivery_config=config.get("config", {}),
                sent_at=result.get("sent_at"),
                delivered_at=result.get("delivered_at"),
                error_message=result.get("error"),
            )

            self.db.add(delivery_record)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to store delivery record: {e}")
            self.db.rollback()

    def get_delivery_status(self, brief_id: UUID) -> List[Dict[str, Any]]:
        """Get delivery status for a brief."""
        try:
            deliveries = (
                self.db.query(BriefDelivery)
                .filter(BriefDelivery.brief_id == brief_id)
                .all()
            )

            return [
                {
                    "id": str(delivery.id),
                    "channel": delivery.channel,
                    "status": delivery.status,
                    "recipient": delivery.recipient,
                    "sent_at": delivery.sent_at,
                    "delivered_at": delivery.delivered_at,
                    "error_message": delivery.error_message,
                }
                for delivery in deliveries
            ]

        except Exception as e:
            logger.error(f"Failed to get delivery status: {e}")
            return []

    async def schedule_delivery(
        self,
        brief_id: UUID,
        delivery_configs: List[Dict[str, Any]],
        delivery_time: datetime,
    ) -> str:
        """Schedule brief delivery for a specific time."""
        try:
            # This would integrate with Celery for scheduled delivery
            from celery import current_app as celery_app

            task = celery_app.send_task(
                "deliver_brief_task",
                args=[str(brief_id), delivery_configs],
                eta=delivery_time,
            )

            logger.info(f"Scheduled delivery for brief {brief_id} at {delivery_time}")
            return task.id

        except Exception as e:
            logger.error(f"Failed to schedule delivery: {e}")
            raise

    def get_delivery_analytics(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get delivery analytics for a user."""
        try:
            from datetime import timedelta

            from sqlalchemy import func

            start_date = datetime.utcnow() - timedelta(days=days)

            # Get delivery statistics
            deliveries = (
                self.db.query(BriefDelivery)
                .join(Brief)
                .filter(
                    and_(
                        Brief.user_id == user_id, BriefDelivery.created_at >= start_date
                    )
                )
                .all()
            )

            total_deliveries = len(deliveries)
            successful_deliveries = len([d for d in deliveries if d.status == "sent"])
            failed_deliveries = len([d for d in deliveries if d.status == "failed"])

            # Channel breakdown
            channel_stats = {}
            for delivery in deliveries:
                channel = delivery.channel
                if channel not in channel_stats:
                    channel_stats[channel] = {"total": 0, "successful": 0, "failed": 0}

                channel_stats[channel]["total"] += 1
                if delivery.status == "sent":
                    channel_stats[channel]["successful"] += 1
                elif delivery.status == "failed":
                    channel_stats[channel]["failed"] += 1

            return {
                "period_days": days,
                "total_deliveries": total_deliveries,
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
                "success_rate": (
                    successful_deliveries / total_deliveries
                    if total_deliveries > 0
                    else 0
                ),
                "channel_stats": channel_stats,
                "most_used_channel": (
                    max(channel_stats.keys(), key=lambda k: channel_stats[k]["total"])
                    if channel_stats
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get delivery analytics: {e}")
            return {}

# Celery task for async delivery
from celery import current_app as celery_app

@celery_app.task(bind=True, max_retries=3)

def deliver_brief_task(self, brief_id: str, delivery_configs: List[Dict[str, Any]]):
    """Celery task for delivering briefs asynchronously."""
    try:
        from app.db.session import SessionLocal

        db = SessionLocal()
        service = BriefDeliveryService(db)

        brief_uuid = UUID(brief_id)
        results = asyncio.run(service.deliver_brief(brief_uuid, delivery_configs))

        db.close()
        return {"brief_id": brief_id, "results": results}

    except Exception as exc:
        logger.error(f"Brief delivery task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
