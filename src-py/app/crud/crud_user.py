from datetime import datetime
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, TYPE_CHECKING, Optional, Union, Dict, Any

from app.core.security import get_password_hash, verify_password
from app.models.user_model import User, UserRole
from app.models.organization_model import Organization
from app.core.config import settings

if TYPE_CHECKING:
    from app.schemas.user_schema import UserCreate, UserUpdate, UserRegister
    from app.models.maintenance_model import MaintenanceRequest

# --- CRUD BÁSICO ---

async def get(db: AsyncSession, *, id: int, organization_id: int | None = None) -> User | None:
    stmt = select(User).where(User.id == id)
    if organization_id:
        stmt = stmt.where(User.organization_id == organization_id)
    stmt = stmt.options(selectinload(User.organization))
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, *, email: str, load_organization: bool = False) -> User | None:
    stmt = select(User).where(User.email == email)
    if load_organization:
        stmt = stmt.options(selectinload(User.organization))
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_multi_by_org(db: AsyncSession, *, organization_id: int | None = None, skip: int = 0, limit: int = 100) -> List[User]:
    stmt = (
        select(User)
        .options(selectinload(User.organization))
        .order_by(User.full_name)
    )
    if organization_id:
        stmt = stmt.where(User.organization_id == organization_id)
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_users_by_role(
    db: AsyncSession,
    *,
    role: UserRole,
    organization_id: int | None = None,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    stmt = select(User).where(
        User.role == role,
        User.is_active == True,
        User.organization_id.is_not(None)
    ).options(selectinload(User.organization))

    if organization_id:
        stmt = stmt.where(User.organization_id == organization_id)
    
    stmt = stmt.order_by(User.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create(db: AsyncSession, *, user_in: "UserCreate", organization_id: int, role: UserRole) -> User:
    hashed_password = get_password_hash(user_in.password)
    
    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hashed_password,
        role=role,
        organization_id=organization_id,
        job_title=getattr(user_in, "job_title", None),
        employee_id=getattr(user_in, "employee_id", None)
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user, ["organization"])
    return db_user

async def create_new_organization_and_user(db: AsyncSession, *, user_in: "UserRegister") -> User:
    """Cria uma nova organização e o primeiro utilizador (MANAGER) para ela."""
    
    db_org = Organization(
        name=user_in.organization_name, 
        sector=user_in.sector
    )
    
    # O primeiro utilizador agora é MANAGER (ex-CLIENTE_DEMO)
    user_role = UserRole.MANAGER 
    
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_role,
        organization=db_org 
    )
    
    db.add(db_org)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user, ["organization"])
    return db_user

async def update(db: AsyncSession, *, db_user: User, user_in: Union["UserUpdate", Dict[str, Any]]) -> User:
    if isinstance(user_in, dict):
        update_data = user_in
    else:
        update_data = user_in.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
    
    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user, ["organization"])
    return db_user

async def update_password(db: AsyncSession, *, db_user: User, new_password: str) -> User:
    hashed_password = get_password_hash(new_password)
    db_user.hashed_password = hashed_password
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate(db: AsyncSession, *, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email=email, load_organization=True)
    if not user:
        return None
    is_correct_password = await run_in_threadpool(verify_password, password, user.hashed_password)
    if not is_correct_password:
        return None
    return user

async def remove(db: AsyncSession, *, db_user: User) -> User:
    await db.delete(db_user)
    await db.commit()
    return db_user

async def count_by_org(db: AsyncSession, *, organization_id: int, role: UserRole | None = None) -> int:
    stmt = select(func.count()).select_from(User).where(User.organization_id == organization_id)
    if role:
        stmt = stmt.where(User.role == role)
    result = await db.execute(stmt)
    return result.scalar_one()

# --- FUNÇÕES ANALÍTICAS ---

async def get_leaderboard_data(db: AsyncSession, *, organization_id: int) -> dict:
    stmt = select(User).where(
        User.organization_id == organization_id, 
        User.role.in_([UserRole.OPERATOR, UserRole.DRIVER])
    ).limit(50)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return {
        "leaderboard": users, 
        "primary_metric_unit": "N/A"
    }

async def get_driver_metrics(db: AsyncSession, *, user: User) -> dict:
    return {
        "distance": 0,
        "hours": 0,
        "fuel_efficiency": 0,
        "alerts": 0
    }

async def get_driver_ranking_context(db: AsyncSession, *, user: User) -> List[Any]:
    return []

async def get_user_stats(db: AsyncSession, *, user_id: int, organization_id: int) -> dict | None:
    from app.models.maintenance_model import MaintenanceRequest

    user = await get(db, id=user_id, organization_id=organization_id)
    if not user:
        return None

    maintenance_count_stmt = select(func.count(MaintenanceRequest.id)).where(MaintenanceRequest.reported_by_id == user_id)
    maintenance_requests_count = (await db.execute(maintenance_count_stmt)).scalar_one_or_none() or 0
    
    return {
        "total_journeys": 0, 
        "maintenance_requests_count": maintenance_requests_count,
        "primary_metric_label": "Ordens",
        "primary_metric_value": 0,
        "primary_metric_unit": "-",
        "performance_by_machine": []
    }

async def get_managers_emails(db: AsyncSession, *, organization_id: int) -> List[str]:
    # Atualizado para buscar os novos cargos de gestão
    stmt = select(User.email).where(
        User.organization_id == organization_id,
        User.role.in_([UserRole.ADMIN, UserRole.MANAGER, UserRole.PCP]),
        User.is_active == True,
        User.email.is_not(None)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())