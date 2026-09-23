"""Alembic environment.

The database URL comes from application settings (``DATABASE_URL``) so migrations always
target the same database as the application. Migrations are executed as an explicit job
(``alembic upgrade head``), never implicitly by API replicas at start-up.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from davos.platform.persistence.base import Base
from davos.platform.persistence.model_registry import register_all_models
from davos.platform.settings.app_settings import AppSettings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

register_all_models()
target_metadata = Base.metadata


def _database_url() -> str:
    return os.environ.get("MIGRATION_DATABASE_URL") or AppSettings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    engine = async_engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
