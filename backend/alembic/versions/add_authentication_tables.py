"""Add authentication tables

Revision ID: auth_tables_001
Revises: df79d18f49e6
Create Date: 2024-08-04 20:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'auth_tables_001'
down_revision = 'df79d18f49e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create OAuth providers table
    op.create_table(
        'oauth_providers',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.String(length=255), nullable=False),
        sa.Column('client_secret_encrypted', sa.Text(), nullable=False),
        sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('provider_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("provider_type IN ('google', 'microsoft', 'slack', 'github')", name='valid_provider_type'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for oauth_providers
    op.create_index('idx_oauth_providers_enabled', 'oauth_providers', ['is_enabled'])
    op.create_index('idx_oauth_providers_org_type', 'oauth_providers', ['organization_id', 'provider_type'])

    # Create auth user sessions table
    op.create_table(
        'auth_user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=False),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('refresh_token_hash')
    )
    
    # Create indexes for auth_user_sessions
    op.create_index('idx_user_sessions_active', 'auth_user_sessions', ['user_id', 'is_revoked', 'expires_at'])
    op.create_index('idx_user_sessions_expires_at', 'auth_user_sessions', ['expires_at'])
    op.create_index('idx_user_sessions_token_hash', 'auth_user_sessions', ['refresh_token_hash'])
    op.create_index('idx_user_sessions_user_id', 'auth_user_sessions', ['user_id'])

    # Create API keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=8), nullable=False),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('allowed_ips', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    
    # Create indexes for api_keys
    op.create_index('idx_api_keys_active', 'api_keys', ['is_active', 'expires_at'])
    op.create_index('idx_api_keys_creator', 'api_keys', ['created_by'])
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_api_keys_org_id', 'api_keys', ['organization_id'])
    op.create_index('idx_api_keys_prefix', 'api_keys', ['key_prefix'])

    # Create login attempts table
    op.create_table(
        'login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('attempt_type', sa.String(length=50), nullable=False),
        sa.Column('failure_reason', sa.String(length=100), nullable=False),
        sa.Column('was_successful', sa.Boolean(), nullable=True),
        sa.Column('additional_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempt_type IN ('email_password', 'oauth', 'api_key')", name='valid_attempt_type'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for login_attempts
    op.create_index('idx_login_attempts_cleanup', 'login_attempts', ['attempted_at'])
    op.create_index('idx_login_attempts_email_time', 'login_attempts', ['email', 'attempted_at'])
    op.create_index('idx_login_attempts_ip_time', 'login_attempts', ['ip_address', 'attempted_at'])
    op.create_index('idx_login_attempts_success', 'login_attempts', ['was_successful', 'attempted_at'])

    # Add authentication-related fields to users table if they don't exist
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove added columns from users table
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'email_verified')
    
    # Drop tables in reverse order
    op.drop_table('login_attempts')
    op.drop_table('api_keys')
    op.drop_table('auth_user_sessions')
    op.drop_table('oauth_providers')