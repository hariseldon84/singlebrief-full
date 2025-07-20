"""Brief preferences and customization service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models.brief import BriefSchedule, BriefTemplate
from app.models.user import Organization, User

logger = logging.getLogger(__name__)

class BriefPreferencesService:
    """Service for managing brief preferences and customization."""

    def __init__(self, db: Session):
        self.db = db

    # Role-based Template Management

    def create_role_based_templates(self, organization_id: UUID) -> List[BriefTemplate]:
        """Create default templates for different roles."""
        try:
            templates = []

            # CEO Template
            ceo_template = self._create_ceo_template(organization_id)
            templates.append(ceo_template)

            # Manager Template
            manager_template = self._create_manager_template(organization_id)
            templates.append(manager_template)

            # Team Lead Template
            team_lead_template = self._create_team_lead_template(organization_id)
            templates.append(team_lead_template)

            # Developer Template
            developer_template = self._create_developer_template(organization_id)
            templates.append(developer_template)

            # Sales Template
            sales_template = self._create_sales_template(organization_id)
            templates.append(sales_template)

            for template in templates:
                self.db.add(template)

            self.db.commit()
            logger.info(
                f"Created {len(templates)} role-based templates for organization {organization_id}"
            )
            return templates

        except Exception as e:
            logger.error(f"Error creating role-based templates: {e}")
            self.db.rollback()
            raise

    def _create_ceo_template(self, organization_id: UUID) -> BriefTemplate:
        """Create CEO-focused template."""
        template_data = {
            "template": """
<div class="brief-container executive-brief">
    <header class="brief-header">
        <h1>Executive Brief - {{ brief.generated_at | format_datetime('%B %d, %Y') }}</h1>
        <div class="summary-stats">
            <span class="stat">{{ stats.critical_items }} Critical Items</span>
            <span class="stat">{{ stats.high_priority_items }} High Priority</span>
            <span class="stat">{{ stats.total_items }} Total Items</span>
        </div>
    </header>

    {% if sections.executive_summary %}
    <section class="executive-summary">
        <h2>{{ sections.executive_summary.title }}</h2>
        <p class="summary-text">{{ sections.executive_summary.content }}</p>
        {% for item in sections.executive_summary.items[:3] %}
        <div class="summary-item">
            <h4>{{ item.title }}</h4>
            <p>{{ item.content | truncate_smart(100) }}</p>
            <span class="confidence">{{ item.score | confidence_indicator }}</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.urgent_items %}
    <section class="urgent-items">
        <h2>🚨 {{ sections.urgent_items.title }}</h2>
        {% for item in sections.urgent_items.items %}
        <div class="urgent-item">
            <h4>{{ item.title }}</h4>
            <p>{{ item.content | truncate_smart(150) }}</p>
            <div class="item-meta">
                <span class="urgency">{{ item.urgency_score | priority_badge }}</span>
                <span class="source">{{ item.source }}</span>
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.action_items %}
    <section class="action-items">
        <h2>📋 Key Decisions & Actions</h2>
        {% for item in sections.action_items.items[:5] %}
        <div class="action-item">
            <p>{{ item.action }}</p>
            <span class="source">From: {{ item.source_title }}</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.trending_topics %}
    <section class="trending-topics">
        <h2>📈 Strategic Trends</h2>
        {% for topic in sections.trending_topics.items[:5] %}
        <div class="trend-item">
            <span class="topic">{{ topic.topic | title }}</span>
            <span class="frequency">{{ topic.mentions }} mentions</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}
</div>

<style>
.executive-brief { font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; }
.brief-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
.summary-stats { display: flex; gap: 2rem; margin-top: 1rem; }
.stat { background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 4px; }
.urgent-item, .action-item { border-left: 4px solid #e74c3c; padding: 1rem; margin: 1rem 0; background: #fef9f9; }
.confidence { float: right; font-size: 1.2em; }
</style>
            """,
            "sections": [
                "executive_summary",
                "urgent_items",
                "action_items",
                "trending_topics",
            ],
            "format": "html",
        }

        sections = {
            "executive_summary": {
                "enabled": True,
                "order": 1,
                "max_items": 3,
                "importance_threshold": 0.8,
            },
            "urgent_items": {
                "enabled": True,
                "order": 2,
                "max_items": 5,
                "urgency_threshold": 0.6,
            },
            "action_items": {"enabled": True, "order": 3, "max_items": 5},
            "trending_topics": {"enabled": True, "order": 4, "max_items": 5},
        }

        styling = {
            "theme": "executive",
            "color_scheme": "blue-gradient",
            "font_family": "Segoe UI",
            "compact_mode": True,
        }

        return BriefTemplate(
            name="Executive Summary (CEO)",
            description="High-level strategic overview for executive leadership",
            template_data=template_data,
            sections=sections,
            styling=styling,
            user_id=None,  # System template
            organization_id=organization_id,
            is_default=False,
            is_shared=True,
            version="1.0.0",
        )

    def _create_manager_template(self, organization_id: UUID) -> BriefTemplate:
        """Create manager-focused template."""
        template_data = {
            "template": """
<div class="brief-container manager-brief">
    <header class="brief-header">
        <h1>Manager's Daily Brief</h1>
        <p class="date">{{ brief.generated_at | format_datetime('%A, %B %d, %Y') }}</p>
    </header>

    {% if sections.urgent_items %}
    <section class="urgent-section">
        <h2>🔥 Immediate Attention Required</h2>
        {% for item in sections.urgent_items.items %}
        <div class="urgent-card">
            <h4>{{ item.title }}</h4>
            <p>{{ item.content | truncate_smart(200) }}</p>
            <div class="item-footer">
                <span class="author">{{ item.author }}</span>
                <span class="time">{{ item.created_at | format_datetime('%H:%M') }}</span>
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.team_updates %}
    <section class="team-section">
        <h2>👥 Team Updates</h2>
        {% for item in sections.team_updates.items %}
        <div class="team-card">
            <h4>{{ item.title }}</h4>
            <p>{{ item.content | truncate_smart(150) }}</p>
            <div class="participants">
                {% for participant in item.participants[:3] %}
                <span class="participant">{{ participant }}</span>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.action_items %}
    <section class="actions-section">
        <h2>✅ Action Items</h2>
        <div class="action-grid">
            {% for item in sections.action_items.items %}
            <div class="action-card">
                <p>{{ item.action }}</p>
                <small>{{ item.source_title }}</small>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}

    {% if sections.project_status %}
    <section class="projects-section">
        <h2>🚀 Project Status</h2>
        {% for item in sections.project_status.items %}
        <div class="project-card">
            <h4>{{ item.title }}</h4>
            <div class="status-bar">
                <span class="status">{{ item.status }}</span>
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}
</div>

<style>
.manager-brief { font-family: 'Inter', sans-serif; max-width: 900px; margin: 0 auto; }
.brief-header { background: #2c3e50; color: white; padding: 1.5rem; border-radius: 6px; margin-bottom: 1.5rem; }
.urgent-card, .team-card, .action-card, .project-card { background: white; border: 1px solid #e1e8ed; border-radius: 6px; padding: 1rem; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.action-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
.urgent-section { border-left: 4px solid #e74c3c; padding-left: 1rem; }
.team-section { border-left: 4px solid #3498db; padding-left: 1rem; }
.actions-section { border-left: 4px solid #2ecc71; padding-left: 1rem; }
.projects-section { border-left: 4px solid #f39c12; padding-left: 1rem; }
</style>
            """,
            "sections": [
                "urgent_items",
                "team_updates",
                "action_items",
                "project_status",
            ],
            "format": "html",
        }

        sections = {
            "urgent_items": {"enabled": True, "order": 1, "max_items": 8},
            "team_updates": {"enabled": True, "order": 2, "max_items": 6},
            "action_items": {"enabled": True, "order": 3, "max_items": 10},
            "project_status": {"enabled": True, "order": 4, "max_items": 5},
        }

        return BriefTemplate(
            name="Manager's Dashboard",
            description="Comprehensive overview for team managers",
            template_data=template_data,
            sections=sections,
            styling={"theme": "manager", "compact_mode": False},
            user_id=None,
            organization_id=organization_id,
            is_shared=True,
            version="1.0.0",
        )

    def _create_team_lead_template(self, organization_id: UUID) -> BriefTemplate:
        """Create team lead-focused template."""
        template_data = {
            "template": """
<div class="brief-container team-lead-brief">
    <header class="brief-header">
        <h1>Team Lead Brief</h1>
        <div class="metrics">
            <div class="metric">
                <span class="value">{{ stats.total_items }}</span>
                <span class="label">Updates</span>
            </div>
            <div class="metric">
                <span class="value">{{ stats.high_priority_items }}</span>
                <span class="label">Priority</span>
            </div>
        </div>
    </header>

    {% if sections.development_metrics %}
    <section class="dev-metrics">
        <h2>💻 Development Activity</h2>
        {% for item in sections.development_metrics.items %}
        <div class="dev-card">
            <h4>{{ item.title }}</h4>
            <p>{{ item.content }}</p>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.team_updates %}
    <section class="team-updates">
        <h2>👥 Team Activity</h2>
        <div class="updates-grid">
            {% for item in sections.team_updates.items %}
            <div class="update-card">
                <h5>{{ item.title }}</h5>
                <p>{{ item.content | truncate_smart(100) }}</p>
                <small>{{ item.participants | length }} participants</small>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}

    {% if sections.action_items %}
    <section class="action-items">
        <h2>⚡ Action Items</h2>
        {% for item in sections.action_items.items %}
        <div class="action-item">
            <input type="checkbox" class="action-checkbox">
            <span class="action-text">{{ item.action }}</span>
            <span class="action-priority">{{ item.priority | priority_badge }}</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}
</div>

<style>
.team-lead-brief { font-family: 'SF Pro Display', sans-serif; max-width: 800px; margin: 0 auto; }
.brief-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
.metrics { display: flex; gap: 2rem; margin-top: 1rem; }
.metric { text-align: center; }
.value { display: block; font-size: 2rem; font-weight: bold; }
.label { font-size: 0.8rem; opacity: 0.8; }
.updates-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
.action-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; border-radius: 4px; margin: 0.5rem 0; }
.action-item:hover { background: #f8f9fa; }
</style>
            """,
            "sections": ["development_metrics", "team_updates", "action_items"],
            "format": "html",
        }

        sections = {
            "development_metrics": {"enabled": True, "order": 1, "max_items": 5},
            "team_updates": {"enabled": True, "order": 2, "max_items": 8},
            "action_items": {"enabled": True, "order": 3, "max_items": 12},
        }

        return BriefTemplate(
            name="Team Lead Dashboard",
            description="Development-focused brief for team leads",
            template_data=template_data,
            sections=sections,
            styling={"theme": "team_lead", "interactive": True},
            user_id=None,
            organization_id=organization_id,
            is_shared=True,
            version="1.0.0",
        )

    def _create_developer_template(self, organization_id: UUID) -> BriefTemplate:
        """Create developer-focused template."""
        template_data = {
            "template": """
<div class="brief-container dev-brief">
    <header class="brief-header">
        <h1>Developer Brief</h1>
        <code class="timestamp">{{ brief.generated_at | format_datetime('%Y-%m-%d %H:%M UTC') }}</code>
    </header>

    {% if sections.development_metrics %}
    <section class="code-section">
        <h2>🔧 Code & Issues</h2>
        {% for item in sections.development_metrics.items %}
        <div class="code-card">
            <h4><code>{{ item.title }}</code></h4>
            <p>{{ item.content }}</p>
            <div class="code-meta">
                <span class="repo">{{ item.source }}</span>
                <span class="status">{{ item.status }}</span>
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.urgent_items %}
    <section class="alerts-section">
        <h2>🚨 Alerts & Blockers</h2>
        {% for item in sections.urgent_items.items %}
        <div class="alert-card">
            <h4>{{ item.title }}</h4>
            <pre>{{ item.content | truncate_smart(300) }}</pre>
            <span class="urgency-level">{{ item.urgency_score | priority_badge }}</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.recent_activity %}
    <section class="activity-section">
        <h2>📝 Recent Activity</h2>
        <div class="activity-list">
            {% for item in sections.recent_activity.items %}
            <div class="activity-item">
                <span class="activity-time">{{ item.updated_at | format_datetime('%H:%M') }}</span>
                <span class="activity-title">{{ item.title }}</span>
                <span class="activity-author">{{ item.author }}</span>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}
</div>

<style>
.dev-brief { font-family: 'Monaco', 'Menlo', monospace; max-width: 900px; margin: 0 auto; background: #1e1e1e; color: #d4d4d4; }
.brief-header { background: #2d2d30; padding: 1.5rem; border-radius: 4px; margin-bottom: 1.5rem; }
.timestamp { color: #9cdcfe; }
.code-card, .alert-card { background: #252526; border: 1px solid #3e3e42; border-radius: 4px; padding: 1rem; margin: 1rem 0; }
.alert-card { border-left: 4px solid #f44747; }
.activity-item { display: flex; gap: 1rem; padding: 0.5rem; border-bottom: 1px solid #3e3e42; }
.activity-time { color: #608b4e; min-width: 60px; }
.activity-author { color: #9cdcfe; margin-left: auto; }
code { background: #1e1e1e; padding: 0.2rem 0.4rem; border-radius: 2px; }
</style>
            """,
            "sections": ["development_metrics", "urgent_items", "recent_activity"],
            "format": "html",
        }

        sections = {
            "development_metrics": {"enabled": True, "order": 1, "max_items": 10},
            "urgent_items": {"enabled": True, "order": 2, "max_items": 5},
            "recent_activity": {"enabled": True, "order": 3, "max_items": 15},
        }

        return BriefTemplate(
            name="Developer Console",
            description="Technical brief for developers",
            template_data=template_data,
            sections=sections,
            styling={"theme": "dark_code", "monospace": True},
            user_id=None,
            organization_id=organization_id,
            is_shared=True,
            version="1.0.0",
        )

    def _create_sales_template(self, organization_id: UUID) -> BriefTemplate:
        """Create sales-focused template."""
        template_data = {
            "template": """
<div class="brief-container sales-brief">
    <header class="brief-header">
        <h1>Sales Brief</h1>
        <div class="sales-metrics">
            <div class="metric">
                <span class="value">{{ stats.total_items }}</span>
                <span class="label">Updates</span>
            </div>
            <div class="metric">
                <span class="value">{{ stats.high_priority_items }}</span>
                <span class="label">Hot Leads</span>
            </div>
        </div>
    </header>

    {% if sections.urgent_items %}
    <section class="hot-leads">
        <h2>🔥 Hot Leads & Urgent Items</h2>
        {% for item in sections.urgent_items.items %}
        <div class="lead-card">
            <h4>{{ item.title }}</h4>
            <p>{{ item.content | truncate_smart(150) }}</p>
            <div class="lead-meta">
                <span class="priority">{{ item.urgency_score | priority_badge }}</span>
                <span class="source">{{ item.source }}</span>
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.action_items %}
    <section class="follow-ups">
        <h2>📞 Follow-ups & Actions</h2>
        {% for item in sections.action_items.items %}
        <div class="followup-item">
            <span class="action">{{ item.action }}</span>
            <span class="priority">{{ item.priority | priority_badge }}</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if sections.trending_topics %}
    <section class="market-trends">
        <h2>📈 Market Trends</h2>
        {% for topic in sections.trending_topics.items %}
        <div class="trend-item">
            <span class="topic">{{ topic.topic | title }}</span>
            <span class="mentions">{{ topic.mentions }} mentions</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}
</div>

<style>
.sales-brief { font-family: 'Roboto', sans-serif; max-width: 800px; margin: 0 auto; }
.brief-header { background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
.sales-metrics { display: flex; gap: 2rem; margin-top: 1rem; }
.metric { text-align: center; background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 4px; }
.lead-card { border-left: 4px solid #FF6B6B; background: #fff5f5; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
.followup-item { display: flex; justify-content: space-between; padding: 0.75rem; margin: 0.5rem 0; background: #f0f9ff; border-radius: 4px; }
.trend-item { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #eee; }
</style>
            """,
            "sections": ["urgent_items", "action_items", "trending_topics"],
            "format": "html",
        }

        sections = {
            "urgent_items": {"enabled": True, "order": 1, "max_items": 8},
            "action_items": {"enabled": True, "order": 2, "max_items": 10},
            "trending_topics": {"enabled": True, "order": 3, "max_items": 5},
        }

        return BriefTemplate(
            name="Sales Dashboard",
            description="Sales-focused brief for leads and opportunities",
            template_data=template_data,
            sections=sections,
            styling={"theme": "sales", "color_scheme": "warm"},
            user_id=None,
            organization_id=organization_id,
            is_shared=True,
            version="1.0.0",
        )

    # Template Customization Methods

    def create_custom_section(
        self,
        template_id: UUID,
        user_id: UUID,
        section_name: str,
        section_config: Dict[str, Any],
    ) -> bool:
        """Add a custom section to a template."""
        try:
            template = (
                self.db.query(BriefTemplate)
                .filter(
                    and_(
                        BriefTemplate.id == template_id,
                        BriefTemplate.user_id == user_id,
                    )
                )
                .first()
            )

            if not template:
                raise ValueError("Template not found or not accessible")

            # Add new section to template
            sections = template.sections.copy()
            sections[section_name] = section_config
            template.sections = sections
            template.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(
                f"Added custom section '{section_name}' to template {template_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error creating custom section: {e}")
            self.db.rollback()
            raise

    def reorder_sections(
        self, template_id: UUID, user_id: UUID, section_order: List[str]
    ) -> bool:
        """Reorder sections in a template."""
        try:
            template = (
                self.db.query(BriefTemplate)
                .filter(
                    and_(
                        BriefTemplate.id == template_id,
                        BriefTemplate.user_id == user_id,
                    )
                )
                .first()
            )

            if not template:
                raise ValueError("Template not found or not accessible")

            # Update section order
            sections = template.sections.copy()
            for i, section_name in enumerate(section_order):
                if section_name in sections:
                    sections[section_name]["order"] = i + 1

            template.sections = sections
            template.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Reordered sections for template {template_id}")
            return True

        except Exception as e:
            logger.error(f"Error reordering sections: {e}")
            self.db.rollback()
            raise

    def update_visual_styling(
        self, template_id: UUID, user_id: UUID, styling_updates: Dict[str, Any]
    ) -> bool:
        """Update visual styling for a template."""
        try:
            template = (
                self.db.query(BriefTemplate)
                .filter(
                    and_(
                        BriefTemplate.id == template_id,
                        BriefTemplate.user_id == user_id,
                    )
                )
                .first()
            )

            if not template:
                raise ValueError("Template not found or not accessible")

            # Update styling
            styling = template.styling.copy() if template.styling else {}
            styling.update(styling_updates)
            template.styling = styling
            template.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Updated styling for template {template_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating styling: {e}")
            self.db.rollback()
            raise

    # Content Filtering and Preferences

    def set_content_filters(
        self, user_id: UUID, organization_id: UUID, filters: Dict[str, Any]
    ) -> bool:
        """Set content filtering preferences for a user."""
        try:
            # This would typically update a UserPreferences model
            # For now, we'll store it as metadata in the user's default template

            default_template = (
                self.db.query(BriefTemplate)
                .filter(
                    and_(
                        BriefTemplate.user_id == user_id,
                        BriefTemplate.is_default == True,
                    )
                )
                .first()
            )

            if not default_template:
                # Create a default template for the user
                default_template = self._create_default_user_template(
                    user_id, organization_id
                )
                self.db.add(default_template)

            # Update template with content filters
            template_data = default_template.template_data.copy()
            template_data["content_filters"] = filters
            default_template.template_data = template_data
            default_template.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Set content filters for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error setting content filters: {e}")
            self.db.rollback()
            raise

    def _create_default_user_template(
        self, user_id: UUID, organization_id: UUID
    ) -> BriefTemplate:
        """Create a default template for a user."""
        template_data = {
            "template": """
<div class="brief-container">
    <h1>{{ brief.title }}</h1>

    {% for section in sections %}
    <section class="brief-section">
        <h2>{{ section.title }}</h2>
        {% for item in section.items %}
        <div class="brief-item">
            <h4>{{ item.title }}</h4>
            <p>{{ item.content | truncate_smart(200) }}</p>
        </div>
        {% endfor %}
    </section>
    {% endfor %}
</div>
            """,
            "sections": [
                "executive_summary",
                "urgent_items",
                "action_items",
                "recent_activity",
            ],
            "format": "html",
            "content_filters": {},
        }

        sections = {
            "executive_summary": {"enabled": True, "order": 1, "max_items": 3},
            "urgent_items": {"enabled": True, "order": 2, "max_items": 5},
            "action_items": {"enabled": True, "order": 3, "max_items": 8},
            "recent_activity": {"enabled": True, "order": 4, "max_items": 10},
        }

        return BriefTemplate(
            name="My Default Brief",
            description="Personalized brief template",
            template_data=template_data,
            sections=sections,
            styling={"theme": "default"},
            user_id=user_id,
            organization_id=organization_id,
            is_default=True,
            is_shared=False,
            version="1.0.0",
        )

    # Template Sharing

    def share_template(
        self, template_id: UUID, user_id: UUID, share_with_team: bool = True
    ) -> bool:
        """Share a template with team or organization."""
        try:
            template = (
                self.db.query(BriefTemplate)
                .filter(
                    and_(
                        BriefTemplate.id == template_id,
                        BriefTemplate.user_id == user_id,
                    )
                )
                .first()
            )

            if not template:
                raise ValueError("Template not found or not accessible")

            template.is_shared = share_with_team
            template.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(
                f"{'Shared' if share_with_team else 'Unshared'} template {template_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error sharing template: {e}")
            self.db.rollback()
            raise

    def clone_template(
        self, source_template_id: UUID, user_id: UUID, new_name: str
    ) -> BriefTemplate:
        """Clone an existing template for customization."""
        try:
            source_template = (
                self.db.query(BriefTemplate)
                .filter(BriefTemplate.id == source_template_id)
                .first()
            )

            if not source_template:
                raise ValueError("Source template not found")

            # Create new template based on source
            cloned_template = BriefTemplate(
                name=new_name,
                description=f"Cloned from {source_template.name}",
                template_data=source_template.template_data.copy(),
                sections=source_template.sections.copy(),
                styling=(
                    source_template.styling.copy() if source_template.styling else {}
                ),
                user_id=user_id,
                organization_id=source_template.organization_id,
                is_default=False,
                is_shared=False,
                version="1.0.0",
            )

            self.db.add(cloned_template)
            self.db.commit()
            self.db.refresh(cloned_template)

            logger.info(f"Cloned template {source_template_id} to {cloned_template.id}")
            return cloned_template

        except Exception as e:
            logger.error(f"Error cloning template: {e}")
            self.db.rollback()
            raise

    # Template Marketplace

    def get_template_marketplace(
        self,
        organization_id: UUID,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get templates from the marketplace."""
        try:
            query = self.db.query(BriefTemplate).filter(BriefTemplate.is_shared == True)

            if category:
                # Filter by category if specified
                query = query.filter(
                    BriefTemplate.styling.contains({"category": category})
                )

            total_count = query.count()
            offset = (page - 1) * page_size
            templates = query.offset(offset).limit(page_size).all()

            marketplace_items = []
            for template in templates:
                # Get usage statistics (placeholder)
                download_count = 0  # Would come from usage analytics
                rating = 4.5  # Would come from user ratings

                marketplace_items.append(
                    {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "author": "Template Creator",  # Would come from user info
                        "category": (
                            template.styling.get("category", "General")
                            if template.styling
                            else "General"
                        ),
                        "tags": (
                            template.styling.get("tags", []) if template.styling else []
                        ),
                        "download_count": download_count,
                        "rating": rating,
                        "preview_url": None,  # Would generate preview
                        "is_featured": (
                            template.styling.get("featured", False)
                            if template.styling
                            else False
                        ),
                        "created_at": template.created_at,
                    }
                )

            return {
                "items": marketplace_items,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
            }

        except Exception as e:
            logger.error(f"Error getting template marketplace: {e}")
            raise

    # Delivery Preferences

    def set_delivery_preferences(
        self, user_id: UUID, preferences: Dict[str, Any]
    ) -> bool:
        """Set delivery preferences for a user."""
        try:
            # This would typically update a UserPreferences model
            # For now, we'll create a schedule with delivery preferences

            schedule_name = f"Default Schedule - {user_id}"
            existing_schedule = (
                self.db.query(BriefSchedule)
                .filter(
                    and_(
                        BriefSchedule.user_id == user_id,
                        BriefSchedule.name == schedule_name,
                    )
                )
                .first()
            )

            if existing_schedule:
                existing_schedule.delivery_channels = preferences.get(
                    "delivery_channels", []
                )
                existing_schedule.updated_at = datetime.utcnow()
            else:
                # Would need to create with a default template
                pass

            self.db.commit()
            logger.info(f"Set delivery preferences for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error setting delivery preferences: {e}")
            self.db.rollback()
            raise
