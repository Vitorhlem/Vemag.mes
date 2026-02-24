from pydantic import BaseModel, constr
from typing import Optional, List
from datetime import date
from app.models.vehicle_model import VehicleStatus

LicensePlateStr = constr(strip_whitespace=True, to_upper=True)

# Schema base com os campos comuns
class VehicleBase(BaseModel):
    brand: str
    model: str
    year: int
    photo_url: Optional[str] = None
    layout_x: Optional[float] = None
    layout_y: Optional[float] = None
    status: Optional[VehicleStatus] = VehicleStatus.AVAILABLE
    sap_resource_code: Optional[str] = None
    current_km: Optional[int] = 0
    current_engine_hours: Optional[float] = 0
    next_maintenance_date: Optional[date] = None
    next_maintenance_km: Optional[int] = None
    maintenance_notes: Optional[str] = None
    identifier: Optional[str] = None
    license_plate: Optional[LicensePlateStr] = None
    
    # Campo de telemetria
    telemetry_device_id: Optional[str] = None

# Schema para a CRIAÇÃO
class VehicleCreate(VehicleBase):
    pass

# Schema para a ATUALIZAÇÃO
class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    layout_x: Optional[float] = None
    layout_y: Optional[float] = None
    photo_url: Optional[str] = None
    status: Optional[VehicleStatus] = None
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
class VehiclePublic(VehicleBase):
    id: int
    # status já herdado de VehicleBase
    last_latitude: Optional[float] = None   
    last_longitude: Optional[float] = None  
    
    model_config = { "from_attributes": True }

# Schema para respostas paginadas
class VehicleListResponse(BaseModel):
    vehicles: List[VehiclePublic]
    total_items: int