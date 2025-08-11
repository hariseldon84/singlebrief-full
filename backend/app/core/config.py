"""
Application configuration settings
"""

import secrets
from typing import List, Optional

from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Basic settings
    PROJECT_NAME: str = "SingleBrief"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Database
    POSTGRES_USER: str = "singlebrief"
    POSTGRES_PASSWORD: str = "singlebrief_dev"
    POSTGRES_DB: str = "singlebrief"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @property
    def DATABASE_URL_COMPUTED(self) -> str:
        # Use explicit DATABASE_URL if provided, otherwise construct from components
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    @property
    def REDIS_URL_COMPUTED(self) -> str:
        # Use explicit REDIS_URL if provided, otherwise construct from components
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v:
            return v
        # Use Redis URL if available, otherwise construct from components
        values = info.data if info.data else {}
        redis_url = values.get('REDIS_URL')
        if redis_url:
            # Replace database number for Celery broker
            return redis_url.rsplit('/', 1)[0] + '/1'
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/1"

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v:
            return v
        # Use Redis URL if available, otherwise construct from components
        values = info.data if info.data else {}
        redis_url = values.get('REDIS_URL')
        if redis_url:
            # Replace database number for Celery backend
            return redis_url.rsplit('/', 1)[0] + '/2'
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/2"

    # Authentication & JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"

    # AI/LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Vector Database
    VECTOR_DB_TYPE: str = "pinecone"  # Options: "weaviate", "pinecone"
    VECTOR_DATABASE_TYPE: str = "pinecone"  # Alias for backward compatibility
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    WEAVIATE_URL: Optional[str] = "http://localhost:8080"
    WEAVIATE_API_KEY: Optional[str] = None

    # External Integrations
    SLACK_CLIENT_ID: Optional[str] = None
    SLACK_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    
    # Developer Tools Integrations
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    JIRA_CLIENT_ID: Optional[str] = None
    JIRA_CLIENT_SECRET: Optional[str] = None
    JIRA_WEBHOOK_SECRET: Optional[str] = None
    
    # Teams Integration (if separate from Microsoft)
    TEAMS_CLIENT_ID: Optional[str] = None
    TEAMS_CLIENT_SECRET: Optional[str] = None

    # Monitoring & Logging
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_PATH: str = "/tmp/uploads"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 60
    
    # Frontend Configuration
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_APP_URL: str = "http://localhost:3000"
    
    # Clerk Authentication
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_WEBHOOK_SECRET: Optional[str] = None

    class Config:
        env_file = "../.env"  # Look for .env in parent directory
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings
