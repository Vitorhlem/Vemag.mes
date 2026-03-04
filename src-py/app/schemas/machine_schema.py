from pydantic import BaseModel, constr
from typing import Optional, List
from datetime import date
from app.models.machine_model import MachineStatus

LicensePlateStr = constr(strip_whitespace=True, to_upper=True)

# Schema base com os campos comuns
class MachineBase(BaseModel):
    brand: str
    model: str
    year: int
    photo_url: Optional[str] = None
    layout_x: Optional[float] = None
    layout_y: Optional[float] = None
    status: Optional[MachineStatus] = MachineStatus.AVAILABLE
    sap_resource_code: Optional[str] = None
    current_km: Optional[int] = 0
    current_engine_hours: Optional[float] = 0
    next_maintenance_date: Optional[date] = None
    next_maintenance_km: Optional[int] = None
    maintenance_notes: Optional[str] = None
    identifier: Optional[str] = None
    license_plate: Optional[LicensePlateStr] = None
    telemetry_device_id: Optional[str] = None

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    layout_x: Optional[float] = None
    layout_y: Optional[float] = None
    photo_url: Optional[str] = None
    status: Optional[MachineStatus] = None
    current_km: Optional[int] = None
    current_engine_hours: Optional[float] = None
    next_maintenance_date: Optional[date] = None
    next_maintenance_km: Optional[int] = None
    maintenance_notes: Optional[str] = None
    identifier: Optional[str] = None
    sap_resource_code: Optional[str] = None
    license_plate: Optional[LicensePlateStr] = None
    telemetry_device_id: Optional[str] = None

# Schema para a RESPOSTA PÚBLICA
class MachinePublic(MachineBase):
    id: int
    last_latitude: Optional[float] = None   
    last_longitude: Optional[float] = None  
    
    model_config = { "from_attributes": True }

# Schema para respostas paginadas
class MachineListResponse(BaseModel):
    machines: List[MachinePublic]
    total_items: int