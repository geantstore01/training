from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from shared.config import Settings
from shared.db.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

if context.is_offline_mode():
    context.configure(url="postgresql+psycopg://", target_metadata=Base.metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(Settings().database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata,
            compare_type=True, include_object=lambda obj, name, type_, reflected, compare_to:
                not (type_ == "table" and name == "spatial_ref_sys"))
        with context.begin_transaction():
            # Évite deux déploiements Alembic concurrents.
            connection.exec_driver_sql("SELECT pg_advisory_xact_lock(731241001)")
            context.run_migrations()
    engine.dispose()
