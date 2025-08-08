"""Initial schema with core models

Revision ID: df79d18f49e6
Revises: 
Create Date: 2025-07-19 22:30:22.852669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'df79d18f49e6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create base tables needed by the system."""
    
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('domain', sa.String(255), unique=True, nullable=True),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('privacy_policy_version', sa.String(20), default='1.0'),
        sa.Column('data_retention_days', sa.Integer(), default=365),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create teams table  
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('role', sa.String(50), nullable=False, default='team_member'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('google_id', sa.String(100), unique=True, nullable=True),
        sa.Column('microsoft_id', sa.String(100), unique=True, nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), default=0),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_2fa_enabled', sa.Boolean(), default=False),
        sa.Column('totp_secret', sa.String(32), nullable=True),
        sa.Column('backup_codes', sa.Text(), nullable=True),
        sa.Column('privacy_settings', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create user_team_memberships association table (consolidated from duplicate tables)
    op.create_table(
        'user_team_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, default='team_member'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('users.id'), nullable=False),
        sa.Column('session_token', sa.String(255), unique=True, nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('device_info', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create user_consents table
    op.create_table(
        'user_consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('users.id'), nullable=False),
        sa.Column('consent_type', sa.String(50), nullable=False),
        sa.Column('is_granted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('consent_text', sa.Text(), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Drop base tables."""
    op.drop_table('user_consents')
    op.drop_table('user_sessions')
    op.drop_table('user_team_memberships')
    op.drop_table('users')
    op.drop_table('teams')
    op.drop_table('organizations')
