from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

# Imports do sistema
from app.crud import crud_vehicle
from app.schemas.vehicle_schema import VehicleCreate, VehicleStatus
from app.models.vehicle_model import Vehicle
from app.adapters.factory import get_erp_adapter

class SAPIntegrationService:
    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.org_id = organization_id
        # Obtém o adaptador da fábrica (Mock ou Real)
        self.adapter = get_erp_adapter()

    # Métodos que apenas repassam a chamada (Delegation)
    async def get_released_production_orders(self) -> List[dict]:
        return await self.adapter.get_production_orders()

    async def get_production_order_by_code(self, op_code: str) -> Optional[dict]:
        return await self.adapter.get_order_details(op_code)

    async def create_production_appointment(self, appointment_data: dict, sap_resource_code: str) -> bool:
        return await self.adapter.send_appointment(appointment_data)

    async def get_open_service_orders(self) -> List[dict]:
        return await self.adapter.get_open_service_orders()

    # Sincronização de Máquinas (Lógica Híbrida: ERP + Banco Local)
    async def sync_machines(self):
        target_machines = [
            "AT000337", "AT000338", "AT000339", "AT000340", "AT000341",
            "AT000237", "AT000238", "AT000205", "AT000212", "AT000214",
            "AT000239", "AT000293", "AT000155", "AT000242", "AT000241",
            "CP000115", "AT000005", "AT000007", "AT000008", "AT000963",
            "AT001314", "AT000912"
        ]
        
        print(f"🎯 [SYNC] Iniciando sincronização via {type(self.adapter).__name__}...")

        for code in target_machines:
            # 1. Busca dados no Adaptador
            item_data = await self.adapter.get_item_details(code)
            if not item_data: continue

            sap_code = item_data.get('ItemCode')
            sap_desc = item_data.get('ItemName') or "Sem Descrição"

            # 2. Verifica Banco Local
            query = select(Vehicle).where(Vehicle.identifier == sap_code)
            result = await self.db.execute(query)
            existing = result.scalars().first()

            if not existing:
                print(f"   ➕ Importando: {sap_code}")
                # (Lógica de inferência de marca mantida...)
                brand = "GENERICA"
                if "ROMI" in sap_desc.upper(): brand = "ROMI"
                elif "NARDINI" in sap_desc.upper(): brand = "NARDINI"
                
                vehicle_in = VehicleCreate(
                    brand=brand[:50], model=sap_desc[:50], year=datetime.now().year,
                    identifier=sap_code, status=VehicleStatus.AVAILABLE,
                    current_km=0, license_plate=sap_code, sap_resource_code=""
                )
                try:
                    await crud_vehicle.create_with_owner(self.db, obj_in=vehicle_in, organization_id=self.org_id)
                except Exception as e:
                    print(f"   ❌ Erro BD: {e}")
                    await self.db.rollback()
        
        print("🏁 [SYNC] Concluído.")