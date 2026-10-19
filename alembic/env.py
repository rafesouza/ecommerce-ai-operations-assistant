
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from backend.app.database import engine
from backend.app.models import Base, Product

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Product so its table is registered in Base.metadata.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without connecting to PostgreSQL."""
    context.configure(
        url=engine.url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the project's SQLAlchemy engine."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
