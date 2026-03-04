from typing import Generator, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.db.session import get_db
from app.models.user_model import User, UserRole
from app import crud

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/token",
    auto_error=True
)

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = await run_in_threadpool(
            jwt.decode, token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception
    
    user = await crud.user.get(db, id=int(user_id))
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Utilizador inativo")
    return current_user

async def get_current_active_manager(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Define quem tem permissão de GESTÃO (Backoffice).
    - ADMIN, MANAGER, PCP, QUALIDADE, LOGÍSTICA e MANUTENÇÃO.
    - OPERADOR e DRIVER ficam de fora.
    """
    authorized_roles = [
        UserRole.ADMIN, 
        UserRole.MANAGER, 
        UserRole.PCP, 
        UserRole.MAINTENANCE, 
        UserRole.QUALITY, 
        UserRole.LOGISTICS
    ]
    
    if current_user.role not in authorized_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O utilizador não tem permissões de gestor.",
        )
    return current_user

async def get_current_active_driver(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Restrito a quem está no chão de fábrica (Operador ou Driver).
    """
    if current_user.role not in [UserRole.DRIVER, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta ação é restrita a operadores/motoristas.",
        )
    return current_user

async def get_current_super_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.ADMIN and current_user.email not in settings.SUPERUSER_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores do sistema."
        )
    return current_user