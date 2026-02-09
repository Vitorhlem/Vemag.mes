import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

# ===========================================================================
# 1. AJUSTE DE PATH (CRÍTICO)
# Adiciona o diretório pai (src-py) ao path do Python para ele encontrar o 'app'
# ===========================================================================
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# ===========================================================================
# 2. IMPORTAÇÕES DO PROJETO
# ===========================================================================
from app.core.config import settings
from app.db.base_class import Base

# IMPORTANTE: Ao importar 'app.models', o arquivo app/models/__init__.py é executado.
# Como ele contém imports de TODOS os seus modelos (ProductionOrder, Vehicle, etc.),
# eles são automaticamente registrados na Base.metadata neste momento.
from app import models 

# ===========================================================================
# 3. CONFIGURAÇÃO DO ALEMBIC
# ===========================================================================
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define a metadata alvo para o autogenerate
target_metadata = Base.metadata

# Sobrescreve a URL do arquivo .ini com a URL das variáveis de ambiente (Docker/Env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URI)

def run_migrations_offline() -> None:
    """Modo offline: gera SQL direto."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Modo online: conecta ao banco e executa."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URI

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())