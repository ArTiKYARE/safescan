"""
SafeScan — Alembic Environment Configuration
Uses sync psycopg2 driver for migrations.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import models to register them with Base.metadata
from app.core.database import Base
import app.models  # noqa: F401 — register all models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with sync engine."""
    import os
    from sqlalchemy import create_engine, pool, event, text
    from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

    # === FIX 1: Читать DATABASE_URL из окружения ===
    url = os.getenv("DATABASE_URL", "")
    if not url:
        url = config.get_main_option("sqlalchemy.url")
    if url and "+asyncpg" in url:
        url = url.replace("+asyncpg", "")

    # === FIX 2: Monkey-patch ENUM.create — проверять существование перед созданием ===
    _original_create = PG_ENUM.create

    def _safe_create(self, bind=None, checkfirst=True, **kw):
        """Создавать ENUM только если его нет в БД"""
        try:
            schema = self.schema or "public"
            # Проверяем через системную таблицу pg_type
            result = bind.execute(
                text(
                    f"SELECT 1 FROM pg_type WHERE typname = '{self.name}' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '{schema}')"
                )
            )
            if result.fetchone():
                return  # Тип уже есть — пропускаем создание
        except Exception:
            pass  # Если проверка не прошла — пробуем создать
        # Пытаемся создать оригинальным методом
        try:
            return _original_create(self, bind=bind, checkfirst=True, **kw)
        except Exception as e:
            if "already exists" in str(e).lower():
                return  # Игнорируем дубликат
            raise  # Другие ошибки — пробрасываем

    PG_ENUM.create = _safe_create
    # === КОНЕЦ PATCH ===

    # === Создаём движок ===
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        pool_pre_ping=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
