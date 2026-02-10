from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import settings

# Cria o "motor" (engine) de conexão com o banco de dados.
engine = create_async_engine(settings.DATABASE_URI, pool_pre_ping=True)

# Cria uma "fábrica" de sessões.
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

# --- CORREÇÃO AQUI ---
# Criamos um alias para que 'async_session' seja a mesma coisa que 'SessionLocal'.
# Isso permite que o production.py importe 'async_session' sem erro.
async_session = SessionLocal
# ---------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Função geradora para ser usada como uma Dependência do FastAPI.
    """
    session: AsyncSession = SessionLocal()
    try:
        # Entrega a sessão para a rota
        yield session
    except Exception:
        # Se um erro na rota não for tratado, desfazemos (rollback)
        await session.rollback()
        raise
    finally:
        # Garante que a sessão seja fechada ao final da requisição
        await session.close()