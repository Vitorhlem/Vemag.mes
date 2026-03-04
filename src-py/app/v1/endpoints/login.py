from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Any

from app import crud, deps
from app.core import auth, email_utils, security
from app.core.config import settings
# Agora Msg existe em token_schema
from app.schemas.token_schema import TokenData, Msg
from app.schemas.user_schema import UserRegister, UserPublic
from app.models.user_model import UserRole
# Import do Celery Task
from sqlalchemy import select
from app.models.user_model import User
from app.tasks.email_tasks import send_email_async
from app.schemas.token_schema import Token
from datetime import timedelta

router = APIRouter()

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str


@router.post("/login/badge", response_model=Token)
async def login_by_badge(
    badge: str = Body(..., embed=True), # Recebe {"badge": "10617"}
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Login rápido via Crachá (Kiosk Mode).
    Busca usuário pelo campo 'employee_id'.
    """
    # Busca o usuário que tenha essa matrícula (employee_id)
    query = select(User).where(User.employee_id == badge)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Crachá não encontrado.")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo.")

    # Gera o Token de Acesso para esse usuário
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserRegister
) -> Any:
    """
    Regista um novo utilizador.
    """
    user_in.email = user_in.email.lower().strip()

    org = await crud.organization.get_organization_by_name(db, name=user_in.organization_name)
    if org:
        raise HTTPException(status_code=400, detail="Uma organização com este nome já está registada.")
    
    user = await crud.user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Um utilizador com este email já está registado.")

    new_user = await crud.user.create_new_organization_and_user(db=db, user_in=user_in)

    if new_user.email in settings.SUPERUSER_EMAILS:
        print(f"✨ Detectado registro de Superusuário ({new_user.email}). Promovendo a ADMIN...")
        new_user.role = UserRole.ADMIN
        
        if new_user.organization:
            db.add(new_user.organization)
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user, attribute_names=["organization"])

    return new_user

@router.post("/token", response_model=TokenData)
async def login_for_access_token(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login."""
    email_input = form_data.username.lower().strip()
    
    user = await auth.authenticate_user(
        db, email=email_input, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Utilizador inativo")
    
    access_token = auth.create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user 
    }
