from pydantic import BaseModel, EmailStr
from typing import Optional, List

from app.models.organization_model import Sector
from app.models.user_model import UserRole
from .organization_schema import OrganizationPublic

class OrganizationNestedInUser(BaseModel):
    id: int
    name: str
    sector: Sector
    model_config = { "from_attributes": True }

class UserBase(BaseModel):
    email: str
    full_name: str
    is_active: bool = True
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    employee_id: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = None
    organization_id: Optional[int] = None
    email: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None 
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    employee_id: Optional[str] = None 
    avatar_url: Optional[str] = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class UserPublic(UserBase):
    id: int
    organization: Optional[OrganizationNestedInUser] = None
    role: UserRole
    is_superuser: bool
    employee_id: Optional[str] = None

    model_config = { "from_attributes": True }

class UserRegister(BaseModel):
    full_name: str
    email: str
    password: str
    organization_name: str
    sector: Sector

class UserStats(BaseModel):
    primary_metric_label: str
    primary_metric_value: float
    primary_metric_unit: str
    maintenance_requests_count: int
    avg_km_per_liter: Optional[float] = None
    avg_cost_per_km: Optional[float] = None
    fleet_avg_km_per_liter: Optional[float] = None

class UserDeviceToken(BaseModel):
    token: str