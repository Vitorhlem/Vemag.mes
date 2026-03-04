from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, deps
from app.models.user_model import User
from app.schemas.organization_schema import (
    OrganizationUpdate,
    OrganizationPublic
)

router = APIRouter()

# --- ENDPOINTS DE ORGANIZAÇÃO ---

@router.get("/organization", response_model=OrganizationPublic)
async def read_organization_settings(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager), 
):
    """
    Retorna os dados da organização do usuário atual.
    """
    organization = await crud.organization.get(db, id=current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organização não encontrada.")
    return organization

@router.put("/organization", response_model=OrganizationPublic)
async def update_organization_settings(
    *,
    db: AsyncSession = Depends(deps.get_db),
    org_in: OrganizationUpdate,
    current_user: User = Depends(deps.get_current_active_manager),
):
    """
    Atualiza as configurações da organização (Nome, CNPJ, Setor, etc).
    Permitido para gestores (Manager, Admin).
    """
    organization = await crud.organization.get(db, id=current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organização não encontrada.")

    # Atualiza no banco
    updated_org = await crud.organization.update(
        db=db, db_obj=organization, obj_in=org_in
    )

    return updated_org