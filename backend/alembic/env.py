"""Alembic environment configuration for SingleBrief database migrations."""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all models to ensure they're registered with SQLAlchemy
from app.core.database import Base
from app.models import *
from app.models.memory import *
from app.models.integration import *
from app.models.audit import *
from app.models.intelligence import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for 'autogenerate' support
target_metadata = Base.metadata

def get_database_url():
    """Get database URL from environment variables with fallback to config."""
    # Try environment variable first (for different environments)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Fallback to alembic.ini configuration
    return config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override the sqlalchemy.url with our custom function
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # Include table name in constraint names for clarity
            render_as_batch=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()