# Import all models here for SQLAlchemy registration
from .auth import OAuthProvider, AuthUserSession, APIKey, LoginAttempt, EmailVerificationToken, PasswordResetToken
from .user import Organization, Team, User, UserConsent, UserSession, UserTeam
from .audit import AuditLog, ConsentRecord, DataAccessLog, PrivacySetting, GDPRRequest, SecurityEvent
from .integration import (
    Integration, OAuthToken, DataSource, IntegrationLog, SyncStatus, IntegrationPermission,
    Connector, ConnectorInstallation, ConnectorHealthCheck, RateLimit, ConfigurationTemplate
)
from .intelligence import Query, AIResponse
from .brief import BriefTemplate, Brief, BriefContentItem, BriefDelivery, BriefSchedule, BriefAnalytics
from .memory import (
    Conversation, ConversationMessage, Decision, UserMemory, TeamMemory, UserPreference, 
    UserBehaviorPattern, PrivacyConsent, DataRetentionPolicy, DataExportRequest, MemoryEmbedding
)
from .team_interrogation import (
    QuestionTemplate, TeamMemberProfile, GeneratedQuestion, QuestionResponse, TeamInsight,
    InteractionFeedback, CommunicationPattern
)
from .team_management import (
    RoleTaxonomy, DesignationTaxonomy, ExpertiseTag, 
    TeamMemberProfileManagement, TeamMemberPlatformAccount, 
    TeamHierarchy, TeamMemberStatusHistory
)

__all__ = [
    # User & Organization
    "User",
    "Organization", 
    "Team",
    "UserTeam",
    "UserSession",
    "UserConsent",
    
    # Authentication
    "OAuthProvider",
    "AuthUserSession", 
    "APIKey",
    "LoginAttempt",
    "EmailVerificationToken",
    "PasswordResetToken",
    
    # Audit & Compliance
    "AuditLog",
    "ConsentRecord",
    "DataAccessLog",
    "PrivacySetting",
    "GDPRRequest",
    "SecurityEvent",
    
    # Integration
    "Integration",
    "OAuthToken",
    "DataSource", 
    "IntegrationLog",
    "SyncStatus",
    "IntegrationPermission",
    "Connector",
    "ConnectorInstallation",
    "ConnectorHealthCheck",
    "RateLimit",
    "ConfigurationTemplate",
    
    # Intelligence & Briefs
    "Query",
    "AIResponse",
    "BriefTemplate",
    "Brief",
    "BriefContentItem",
    "BriefDelivery",
    "BriefSchedule",
    "BriefAnalytics",
    
    # Memory
    "Conversation",
    "ConversationMessage",
    "Decision",
    "UserMemory",
    "TeamMemory",
    "UserPreference",
    "UserBehaviorPattern",
    "PrivacyConsent", 
    "DataRetentionPolicy",
    "DataExportRequest",
    "MemoryEmbedding",
    
    # Team Interrogation
    "QuestionTemplate",
    "TeamMemberProfile",
    "GeneratedQuestion",
    "QuestionResponse",
    "TeamInsight",
    "InteractionFeedback",
    "CommunicationPattern",
    
    # Team Management
    "RoleTaxonomy",
    "DesignationTaxonomy", 
    "ExpertiseTag",
    "TeamMemberProfileManagement",
    "TeamMemberPlatformAccount",
    "TeamHierarchy",
    "TeamMemberStatusHistory",
]
