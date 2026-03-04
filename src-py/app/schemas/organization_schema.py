from pydantic import BaseModel
from typing import Optional, List

from app.models.organization_model import Sector
from app.models.user_model import UserRole


class UserNestedInOrganization(BaseModel):
    id: int
    role: UserRole
    model_config = { "from_attributes": True }


class OrganizationBase(BaseModel):
    name: str
    sector: Sector
    cnpj: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None

class OrganizationNestedInUser(BaseModel):
    id: int
    name: str
    sector: Sector
    model_config = { "from_attributes": True }


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[Sector] = None
    cnpj: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None


class OrganizationPublic(OrganizationBase):
    id: int
    users: List[UserNestedInOrganization] = []
    model_config = { "from_attributes": True }
