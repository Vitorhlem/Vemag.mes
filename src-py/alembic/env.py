import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

# 1. AJUSTE DE PATH (CRÍTICO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.core.config import settings
from app.db.base_class import Base
from app import models 

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ===========================================================================
# 🔥 A SOLUÇÃO: FORÇAR A LEITURA DO DOCKER PRIMEIRO
# ===========================================================================
def get_database_url():
    # 1º Tenta pegar a variável exata que o Docker Compose injeta
    env_url = os.environ.get("DATABASE_URI") or os.environ.get("DATABASE_URL")
    
    if env_url:
        print(f"🔗 [ALEMBIC] Usando banco do Docker: {env_url.split('@')[-1]}")
        return env_url
        
    # 2º Se rodar fora do Docker, usa o que tá no código
    print(f"🔗 [ALEMBIC] Usando banco do settings local: {settings.DATABASE_URI.split('@')[-1]}")
    return settings.DATABASE_URI

# Sobrescreve pro offline mode
config.set_main_option("sqlalchemy.url", get_database_url())

def run_migrations_offline() -> None:
    """Modo offline: gera SQL direto."""
    url = get_database_url()
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
    
    # 🔥 Força a URL correta aqui antes de conectar
    configuration["sqlalchemy.url"] = get_database_url()

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