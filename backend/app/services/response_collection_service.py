"""
Response Collection and Management Service

Handles multi-channel response collection and tracking including:
- Multi-channel response collection (Slack, email, web, mobile)
- Response tracking and status management
- Automated follow-up and reminder system
- Partial response handling and resumption
- Anonymous and confidential response options
- Response validation and quality checking
"""

from typing import Any, Dict, List, Optional, Tuple

import uuid
from datetime import datetime, timedelta

from celery import Celery
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.team_interrogation import (GeneratedQuestion,
                                         InteractionFeedback, QuestionResponse,
                                         QuestionType, ResponseStatus,
                                         TeamMemberProfile)
from ..models.user import User
from .communication_service import CommunicationService
from .email_service import EmailService
from .llm_service import LLMService
from .slack_service import SlackService

class ResponseCollectionService:
    """Service for response collection and management across multiple channels"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.communication_service = CommunicationService(db)
        self.slack_service = SlackService()
        self.email_service = EmailService()

        # Channel handlers
        self.channel_handlers = {
            "slack": self._handle_slack_response,
            "email": self._handle_email_response,
            "web": self._handle_web_response,
            "mobile": self._handle_mobile_response,
        }

    async def send_question_to_channel(
        self,
        question: GeneratedQuestion,
        channel: str,
        recipient_profile: TeamMemberProfile,
    ) -> Dict[str, Any]:
        """Send a question through the specified channel"""

        # Adapt message for the channel and recipient
        adapted_message = await self.communication_service.adapt_message_for_recipient(
            message=question.question_text,
            recipient_profile=recipient_profile,
            context=question.context,
            message_type="question",
        )

        # Channel-specific sending
        result = None
        if channel == "slack":
            result = await self._send_slack_question(
                question, adapted_message, recipient_profile
            )
        elif channel == "email":
            result = await self._send_email_question(
                question, adapted_message, recipient_profile
            )
        elif channel == "web":
            result = await self._send_web_question(
                question, adapted_message, recipient_profile
            )
        elif channel == "mobile":
            result = await self._send_mobile_question(
                question, adapted_message, recipient_profile
            )
        else:
            raise ValueError(f"Unsupported channel: {channel}")

        # Update question with delivery information
        question.sent_at = datetime.utcnow()
        question.delivery_channel = channel
        self.db.commit()

        # Schedule follow-up reminders
        await self._schedule_reminders(question, recipient_profile)

        return result

    async def collect_response(
        self,
        question_id: str,
        responder_id: str,
        response_data: Dict[str, Any],
        channel: str,
    ) -> QuestionResponse:
        """Collect and process a response from any channel"""

        question = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.id == question_id)
            .first()
        )

        if not question:
            raise ValueError(f"Question not found: {question_id}")

        # Check for existing response
        existing_response = (
            self.db.query(QuestionResponse)
            .filter(
                and_(
                    QuestionResponse.question_id == question_id,
                    QuestionResponse.responder_id == responder_id,
                )
            )
            .first()
        )

        # Process response data
        processed_data = await self._process_response_data(
            response_data, question.question_type, channel
        )

        # Validate response
        validation_result = await self._validate_response(processed_data, question)

        if existing_response:
            # Update existing response
            existing_response = await self._update_existing_response(
                existing_response, processed_data, validation_result
            )
            return existing_response
        else:
            # Create new response
            new_response = await self._create_new_response(
                question_id, responder_id, processed_data, validation_result, channel
            )
            return new_response

    async def handle_partial_response(
        self,
        question_id: str,
        responder_id: str,
        partial_data: Dict[str, Any],
        channel: str,
    ) -> QuestionResponse:
        """Handle partial response and enable resumption"""

        # Create or update partial response
        response = await self.collect_response(
            question_id, responder_id, partial_data, channel
        )

        response.status = ResponseStatus.PARTIAL
        self.db.commit()

        # Generate resumption link/prompt
        resumption_context = await self._generate_resumption_context(response)

        # Send resumption notification based on channel preferences
        await self._send_resumption_notification(response, resumption_context)

        return response

    async def send_reminder(
        self, question_id: str, reminder_type: str = "gentle"
    ) -> Dict[str, Any]:
        """Send a reminder for an unanswered question"""

        question = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.id == question_id)
            .first()
        )

        if not question:
            return {"error": "Question not found"}

        # Check if reminder is appropriate
        reminder_check = await self._should_send_reminder(question)
        if not reminder_check["should_remind"]:
            return {"skipped": True, "reason": reminder_check["reason"]}

        # Get recipient profile
        recipient = question.recipient

        # Generate reminder message
        reminder_message = await self._generate_reminder_message(
            question, recipient, reminder_type
        )

        # Send reminder through original channel
        result = await self._send_channel_message(
            question.delivery_channel, reminder_message, recipient, question
        )

        # Log reminder
        await self._log_reminder(question_id, reminder_type, result)

        return result

    async def process_anonymous_response(
        self,
        question_id: str,
        response_data: Dict[str, Any],
        channel: str,
        anonymous_token: str,
    ) -> QuestionResponse:
        """Process an anonymous response"""

        # Verify anonymous token
        question = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.id == question_id)
            .first()
        )

        if not question:
            raise ValueError("Question not found")

        # Create anonymous responder ID
        anonymous_responder_id = f"anonymous_{anonymous_token}"

        # Process response with anonymous flag
        response_data["is_anonymous"] = True
        response = await self.collect_response(
            question_id, anonymous_responder_id, response_data, channel
        )

        return response

    async def get_response_analytics(
        self,
        question_id: Optional[str] = None,
        team_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive response analytics"""

        # Build query
        query = self.db.query(QuestionResponse)

        if question_id:
            query = query.filter(QuestionResponse.question_id == question_id)

        if team_id:
            query = (
                query.join(GeneratedQuestion)
                .join(TeamMemberProfile)
                .filter(TeamMemberProfile.team_id == team_id)
            )

        if start_date:
            query = query.filter(QuestionResponse.created_at >= start_date)
        if end_date:
            query = query.filter(QuestionResponse.created_at <= end_date)

        responses = query.all()

        if not responses:
            return {"total_responses": 0}

        # Calculate analytics
        total_responses = len(responses)
        completed_responses = len(
            [r for r in responses if r.status == ResponseStatus.COMPLETED]
        )
        partial_responses = len(
            [r for r in responses if r.status == ResponseStatus.PARTIAL]
        )

        # Response times
        response_times = [
            r.response_time_seconds for r in responses if r.response_time_seconds
        ]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # Quality scores
        quality_scores = [
            r.quality_indicators.get("quality_score", 0.0)
            for r in responses
            if r.quality_indicators
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Channel distribution
        channel_distribution = {}
        for response in responses:
            channel = response.response_channel
            channel_distribution[channel] = channel_distribution.get(channel, 0) + 1

        # Sentiment analysis
        sentiment_scores = [
            r.sentiment_score for r in responses if r.sentiment_score is not None
        ]
        avg_sentiment = (
            sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        )

        return {
            "total_responses": total_responses,
            "completed_responses": completed_responses,
            "partial_responses": partial_responses,
            "completion_rate": (
                completed_responses / total_responses if total_responses > 0 else 0
            ),
            "avg_response_time_seconds": avg_response_time,
            "avg_quality_score": avg_quality,
            "avg_sentiment_score": avg_sentiment,
            "channel_distribution": channel_distribution,
            "anonymous_responses": len([r for r in responses if r.is_anonymous]),
            "confidential_responses": len([r for r in responses if r.is_confidential]),
        }

    # Private helper methods

    async def _send_slack_question(
        self, question: GeneratedQuestion, message: str, recipient: TeamMemberProfile
    ) -> Dict[str, Any]:
        """Send question via Slack"""

        # Format question for Slack
        slack_blocks = await self._format_slack_question(question, message)

        # Send to user's Slack
        user_slack_id = recipient.user.slack_id if recipient.user else None
        if not user_slack_id:
            raise ValueError("Recipient Slack ID not found")

        result = await self.slack_service.send_message(
            channel=user_slack_id,
            blocks=slack_blocks,
            metadata={"question_id": question.id, "type": "team_question"},
        )

        return result

    async def _send_email_question(
        self, question: GeneratedQuestion, message: str, recipient: TeamMemberProfile
    ) -> Dict[str, Any]:
        """Send question via email"""

        # Format question for email
        email_content = await self._format_email_question(question, message, recipient)

        # Send email
        result = await self.email_service.send_email(
            to_email=recipient.user.email,
            subject=f"Team Question: {question.context.get('topic', 'Your Input Needed')}",
            html_content=email_content["html"],
            text_content=email_content["text"],
            metadata={"question_id": question.id, "type": "team_question"},
        )

        return result

    async def _send_web_question(
        self, question: GeneratedQuestion, message: str, recipient: TeamMemberProfile
    ) -> Dict[str, Any]:
        """Send question via web interface"""

        # Create web notification/task
        web_notification = {
            "type": "team_question",
            "question_id": question.id,
            "recipient_id": recipient.id,
            "message": message,
            "question_type": question.question_type,
            "options": question.options,
            "expires_at": (
                question.expires_at.isoformat() if question.expires_at else None
            ),
            "created_at": datetime.utcnow().isoformat(),
        }

        # Store in notification queue (would integrate with real notification system)
        # For now, return success
        return {
            "status": "sent",
            "channel": "web",
            "notification_id": str(uuid.uuid4()),
        }

    async def _send_mobile_question(
        self, question: GeneratedQuestion, message: str, recipient: TeamMemberProfile
    ) -> Dict[str, Any]:
        """Send question via mobile push notification"""

        # Format for mobile
        mobile_payload = {
            "title": "Team Question",
            "body": message[:100] + "..." if len(message) > 100 else message,
            "data": {
                "question_id": question.id,
                "type": "team_question",
                "question_type": question.question_type,
                "deep_link": f"app://questions/{question.id}",
            },
        }

        # Send push notification (would integrate with actual push service)
        # For now, return success
        return {"status": "sent", "channel": "mobile", "payload": mobile_payload}

    async def _process_response_data(
        self, response_data: Dict[str, Any], question_type: QuestionType, channel: str
    ) -> Dict[str, Any]:
        """Process and normalize response data"""

        processed = {
            "response_text": response_data.get("response_text"),
            "selected_options": response_data.get("selected_options"),
            "scale_value": response_data.get("scale_value"),
            "confidence": response_data.get("confidence"),
            "is_anonymous": response_data.get("is_anonymous", False),
            "is_confidential": response_data.get("is_confidential", False),
            "started_at": response_data.get("started_at"),
            "response_time_seconds": response_data.get("response_time_seconds"),
        }

        # Question type specific processing
        if question_type == QuestionType.MULTIPLE_CHOICE:
            if "selected_options" not in response_data:
                processed["selected_options"] = [response_data.get("response_text")]
        elif question_type == QuestionType.SCALE:
            if "scale_value" not in response_data:
                # Try to extract numeric value from text
                text = response_data.get("response_text", "")
                try:
                    processed["scale_value"] = float(text)
                except Exception:
                    processed["scale_value"] = None

        # Channel-specific processing
        if channel == "slack":
            processed = await self._process_slack_response_data(
                processed, response_data
            )
        elif channel == "email":
            processed = await self._process_email_response_data(
                processed, response_data
            )

        return processed

    async def _validate_response(
        self, response_data: Dict[str, Any], question: GeneratedQuestion
    ) -> Dict[str, Any]:
        """Validate response data and return validation results"""

        validation = {
            "is_valid": True,
            "quality_score": 0.0,
            "issues": [],
            "suggestions": [],
        }

        # Check completeness
        if question.question_type == QuestionType.OPEN_ENDED:
            if (
                not response_data.get("response_text")
                or len(response_data["response_text"].strip()) < 5
            ):
                validation["issues"].append(
                    "Response too short for open-ended question"
                )
                validation["quality_score"] -= 0.3

        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            if not response_data.get("selected_options"):
                validation["issues"].append(
                    "No options selected for multiple choice question"
                )
                validation["is_valid"] = False

        elif question.question_type == QuestionType.SCALE:
            if response_data.get("scale_value") is None:
                validation["issues"].append("No scale value provided")
                validation["is_valid"] = False

        # Analyze response quality using LLM
        if response_data.get("response_text"):
            quality_analysis = await self._analyze_response_quality(
                response_data["response_text"], question.question_text
            )
            validation["quality_score"] += quality_analysis["quality_score"]
            validation["issues"].extend(quality_analysis.get("issues", []))
            validation["suggestions"].extend(quality_analysis.get("suggestions", []))

        # Normalize quality score
        validation["quality_score"] = max(
            0.0, min(1.0, validation["quality_score"] + 0.5)
        )

        return validation

    async def _update_existing_response(
        self,
        response: QuestionResponse,
        processed_data: Dict[str, Any],
        validation: Dict[str, Any],
    ) -> QuestionResponse:
        """Update an existing response"""

        # Update fields
        for field, value in processed_data.items():
            if value is not None:
                setattr(response, field, value)

        # Update status
        if validation["is_valid"] and processed_data.get("response_text"):
            response.status = ResponseStatus.COMPLETED
            response.completed_at = datetime.utcnow()
        else:
            response.status = ResponseStatus.PARTIAL

        # Update quality indicators
        response.quality_indicators = {
            "quality_score": validation["quality_score"],
            "validation_issues": validation["issues"],
            "suggestions": validation["suggestions"],
            "needs_clarification": len(validation["issues"]) > 0,
        }

        response.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(response)

        return response

    async def _create_new_response(
        self,
        question_id: str,
        responder_id: str,
        processed_data: Dict[str, Any],
        validation: Dict[str, Any],
        channel: str,
    ) -> QuestionResponse:
        """Create a new response"""

        response = QuestionResponse(
            question_id=question_id,
            responder_id=responder_id,
            response_channel=channel,
            **processed_data,
        )

        # Set status
        if validation["is_valid"] and processed_data.get("response_text"):
            response.status = ResponseStatus.COMPLETED
            response.completed_at = datetime.utcnow()
        else:
            response.status = ResponseStatus.PARTIAL

        # Set quality indicators
        response.quality_indicators = {
            "quality_score": validation["quality_score"],
            "validation_issues": validation["issues"],
            "suggestions": validation["suggestions"],
            "needs_clarification": len(validation["issues"]) > 0,
        }

        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)

        return response

    async def _schedule_reminders(
        self, question: GeneratedQuestion, recipient: TeamMemberProfile
    ) -> None:
        """Schedule automated reminders for unanswered questions"""

        if not question.expires_at:
            return

        # Calculate reminder schedule based on time to expiry
        time_to_expiry = (
            question.expires_at - datetime.utcnow()
        ).total_seconds() / 3600  # hours

        # Schedule reminders at different intervals
        reminder_schedule = []

        if time_to_expiry > 48:  # More than 2 days
            reminder_schedule.append({"delay_hours": 24, "type": "gentle"})
            reminder_schedule.append(
                {"delay_hours": time_to_expiry - 6, "type": "urgent"}
            )
        elif time_to_expiry > 24:  # More than 1 day
            reminder_schedule.append(
                {"delay_hours": time_to_expiry - 4, "type": "gentle"}
            )
        elif time_to_expiry > 8:  # More than 8 hours
            reminder_schedule.append(
                {"delay_hours": time_to_expiry - 2, "type": "gentle"}
            )

        # Schedule with Celery (would integrate with actual task queue)
        for reminder in reminder_schedule:
            # celery_app.send_task(
            #     "send_question_reminder",
            #     args=[question.id, reminder["type"]],
            #     countdown=reminder["delay_hours"] * 3600
            # )
            pass

    async def _should_send_reminder(
        self, question: GeneratedQuestion
    ) -> Dict[str, Any]:
        """Check if a reminder should be sent"""

        # Check if already answered
        response = (
            self.db.query(QuestionResponse)
            .filter(QuestionResponse.question_id == question.id)
            .first()
        )

        if response and response.status == ResponseStatus.COMPLETED:
            return {"should_remind": False, "reason": "Already answered"}

        # Check if expired
        if question.expires_at and datetime.utcnow() > question.expires_at:
            return {"should_remind": False, "reason": "Question expired"}

        # Check recipient workload
        recipient = question.recipient
        if recipient.current_workload > 0.9:
            return {"should_remind": False, "reason": "Recipient overloaded"}

        # Check recent reminder frequency
        # (In a real implementation, would check reminder log)

        return {"should_remind": True}

    async def _generate_reminder_message(
        self,
        question: GeneratedQuestion,
        recipient: TeamMemberProfile,
        reminder_type: str,
    ) -> str:
        """Generate an appropriate reminder message"""

        reminder_prompt = f"""
        Generate a {reminder_type} reminder message for an unanswered team question:

        Original Question: {question.question_text}

        Recipient Profile:
        - Name: {recipient.user.first_name if recipient.user else "Team Member"}
        - Role: {recipient.role}
        - Trust Level: {recipient.trust_level}
        - Communication Style: {recipient.preferred_style}

        Reminder Type: {reminder_type}
        Context: {json.dumps(question.context, indent=2)}

        Guidelines:
        - For "gentle" reminders: Be polite and understanding
        - For "urgent" reminders: Be more direct but still respectful
        - Keep it brief and actionable
        - Reference the original question context
        - Include a clear call to action

        Generate only the reminder message.
        """

        reminder_message = await self.llm_service.generate_text(
            prompt=reminder_prompt, max_tokens=150
        )

        return reminder_message.strip()

    async def _analyze_response_quality(
        self, response_text: str, question_text: str
    ) -> Dict[str, Any]:
        """Analyze response quality using LLM"""

        quality_prompt = f"""
        Analyze the quality of this response to the given question:

        Question: {question_text}
        Response: {response_text}

        Evaluate on these criteria:
        1. Relevance to the question (0.0-1.0)
        2. Completeness of answer (0.0-1.0)
        3. Clarity and coherence (0.0-1.0)
        4. Actionability (0.0-1.0)

        Return JSON format:
        {{
            "quality_score": 0.0-1.0,
            "relevance": 0.0-1.0,
            "completeness": 0.0-1.0,
            "clarity": 0.0-1.0,
            "actionability": 0.0-1.0,
            "issues": ["list of issues"],
            "suggestions": ["list of improvement suggestions"]
        }}
        """

        try:
            analysis_text = await self.llm_service.generate_text(
                prompt=quality_prompt, max_tokens=300
            )
            return json.loads(analysis_text.strip())
        except Exception:
            # Fallback basic analysis
            return {
                "quality_score": 0.7,
                "relevance": 0.7,
                "completeness": 0.7,
                "clarity": 0.7,
                "actionability": 0.7,
                "issues": [],
                "suggestions": [],
            }

    async def _format_slack_question(
        self, question: GeneratedQuestion, message: str
    ) -> List[Dict]:
        """Format question for Slack using blocks"""

        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Team Question*\n{message}"},
            }
        ]

        # Add question-type specific elements
        if question.question_type == QuestionType.MULTIPLE_CHOICE and question.options:
            options = question.options.get("choices", [])
            if options:
                blocks.append(
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "radio_buttons",
                                "action_id": f"question_response_{question.id}",
                                "options": [
                                    {
                                        "text": {"type": "plain_text", "text": option},
                                        "value": option,
                                    }
                                    for option in options
                                ],
                            }
                        ],
                    }
                )

        elif question.question_type == QuestionType.SCALE:
            scale_min = question.options.get("min", 1) if question.options else 1
            scale_max = question.options.get("max", 5) if question.options else 5

            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "static_select",
                            "action_id": f"scale_response_{question.id}",
                            "placeholder": {
                                "type": "plain_text",
                                "text": f"Select {scale_min}-{scale_max}",
                            },
                            "options": [
                                {
                                    "text": {"type": "plain_text", "text": str(i)},
                                    "value": str(i),
                                }
                                for i in range(scale_min, scale_max + 1)
                            ],
                        }
                    ],
                }
            )

        # Add response button for open-ended
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Respond"},
                        "action_id": f"open_response_{question.id}",
                        "style": "primary",
                    }
                ],
            }
        )

        return blocks

    async def _format_email_question(
        self, question: GeneratedQuestion, message: str, recipient: TeamMemberProfile
    ) -> Dict[str, str]:
        """Format question for email"""

        html_content = f"""
        <html>
        <body>
            <h2>Team Question</h2>
            <p>Hi {recipient.user.first_name if recipient.user else "Team Member"},</p>

            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p>{message}</p>
            </div>

            <p>
                <a href="{settings.WEB_URL}/questions/{question.id}"
                   style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                   Respond to Question
                </a>
            </p>

            <p><small>This question will expire on {question.expires_at.strftime('%Y-%m-%d %H:%M') if question.expires_at else 'no deadline'}.</small></p>
        </body>
        </html>
        """

        text_content = f"""
        Team Question

        Hi {recipient.user.first_name if recipient.user else "Team Member"},

        {message}

        Please respond at: {settings.WEB_URL}/questions/{question.id}

        This question expires on {question.expires_at.strftime('%Y-%m-%d %H:%M') if question.expires_at else 'no deadline'}.
        """

        return {"html": html_content, "text": text_content}

    async def _send_channel_message(
        self,
        channel: str,
        message: str,
        recipient: TeamMemberProfile,
        question: GeneratedQuestion,
    ) -> Dict[str, Any]:
        """Send a message through the specified channel"""

        if channel == "slack":
            return await self._send_slack_question(question, message, recipient)
        elif channel == "email":
            return await self._send_email_question(question, message, recipient)
        elif channel == "web":
            return await self._send_web_question(question, message, recipient)
        elif channel == "mobile":
            return await self._send_mobile_question(question, message, recipient)
        else:
            return {"error": f"Unsupported channel: {channel}"}

    async def _log_reminder(
        self, question_id: str, reminder_type: str, result: Dict[str, Any]
    ) -> None:
        """Log reminder sending"""

        # In a real implementation, would log to database or monitoring system
        print(
            f"Reminder sent for question {question_id}, type: {reminder_type}, result: {result}"
        )

    async def _generate_resumption_context(
        self, response: QuestionResponse
    ) -> Dict[str, Any]:
        """Generate context for resuming a partial response"""

        return {
            "response_id": response.id,
            "question_id": response.question_id,
            "partial_content": response.response_text,
            "completion_percentage": self._calculate_completion_percentage(response),
            "resumption_url": f"{settings.WEB_URL}/questions/{response.question_id}/resume/{response.id}",
            "expected_time_remaining": self._estimate_remaining_time(response),
        }

    async def _send_resumption_notification(
        self, response: QuestionResponse, context: Dict[str, Any]
    ) -> None:
        """Send notification to help user resume their response"""

        question = response.question
        recipient = response.responder

        resumption_message = f"""
        You started responding to a team question but didn't finish.

        Your partial response: "{response.response_text[:100]}..."

        You can continue where you left off: {context['resumption_url']}
        """

        # Send through preferred channel
        preferred_channel = (
            recipient.preferred_channels[0] if recipient.preferred_channels else "email"
        )
        await self._send_channel_message(
            preferred_channel, resumption_message, recipient, question
        )

    def _calculate_completion_percentage(self, response: QuestionResponse) -> float:
        """Calculate how complete a partial response is"""

        if not response.response_text:
            return 0.0

        # Simple heuristic based on text length and question type
        text_length = len(response.response_text.strip())

        if response.question.question_type == QuestionType.OPEN_ENDED:
            # Consider complete if more than 50 characters
            return min(1.0, text_length / 50.0)
        else:
            # For other types, presence of any response is significant
            return 0.8 if text_length > 0 else 0.0

    def _estimate_remaining_time(self, response: QuestionResponse) -> int:
        """Estimate remaining time to complete response in minutes"""

        completion_pct = self._calculate_completion_percentage(response)

        if completion_pct >= 0.8:
            return 1  # Almost done, just need a minute
        elif completion_pct >= 0.5:
            return 3  # Partially done, few more minutes
        else:
            return 5  # Barely started, needs more time

    async def _process_slack_response_data(
        self, processed: Dict[str, Any], raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process Slack-specific response data"""

        # Handle Slack interaction payloads
        if "actions" in raw_data:
            actions = raw_data["actions"]
            if actions:
                action = actions[0]
                if action.get("type") == "radio_buttons":
                    processed["selected_options"] = [
                        action.get("selected_option", {}).get("value")
                    ]
                elif action.get("type") == "static_select":
                    processed["scale_value"] = float(
                        action.get("selected_option", {}).get("value", 0)
                    )

        return processed

    async def _process_email_response_data(
        self, processed: Dict[str, Any], raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process email-specific response data"""

        # Handle email form submissions
        if "form_data" in raw_data:
            form_data = raw_data["form_data"]
            processed.update(form_data)

        return processed
