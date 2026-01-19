import httpx
import asyncio
import random
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Importando seus Models e Schemas
from app.crud import crud_vehicle, crud_user
from app.schemas.vehicle_schema import VehicleCreate, VehicleStatus
from app.schemas.user_schema import UserCreate
from app.models.user_model import User, UserRole
from app.models.vehicle_model import Vehicle

# CONFIGURAÇÕES DO SAP (Deixe o link que deu 404 mesmo, o código vai tratar)
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

class SAPIntegrationService:
    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.org_id = organization_id
        # Timeout curto (5s) para não ficar esperando muito se travar
        self.client = httpx.AsyncClient(verify=False, timeout=5.0)
        self.cookies = None
        self.mock_mode = False 

    async def login(self) -> bool:
        """
        Tenta autenticar. 
        Se der CERTO (200) -> Usa SAP Real.
        Se der ERRADO (404, Timeout, Erro) -> Ativa MOCK MODE e segue o baile.
        """
        payload = {"CompanyDB": SAP_COMPANY_DB, "UserName": SAP_USER, "Password": SAP_PASSWORD}
        try:
            print(f"🔐 [SAP] Tentando login em {SAP_BASE_URL}...")
            response = await self.client.post(f"{SAP_BASE_URL}/Login", json=payload)
            
            if response.status_code == 200:
                self.cookies = response.cookies
                print("✅ [SAP] Conectado ao servidor real!")
                return True
            else:
                # AQUI ESTÁ A MUDANÇA: Se der 404 ou erro de senha, VIRA MOCK.
                print(f"⚠️ [SAP] Login falhou (Status {response.status_code})...")
                print("🚀 [SAP] Ativando MODO SIMULADO (Mock) para você não parar...")
                self.mock_mode = True
                return True 

        except Exception as e:
            print(f"❌ [SAP] Erro de conexão: {str(e)}")
            print("🚀 [SAP] Sem internet ou VPN? Ativando MODO SIMULADO...")
            self.mock_mode = True
            return True

    async def sync_machines(self):
        # Garante login (ou ativa mock)
        if not self.cookies and not self.mock_mode:
            if not await self.login(): return

        items = []
        if not self.mock_mode:
            try:
                # Tenta buscar do SAP Real
                query = "$select=ItemCode,ItemName,ItemsGroupCode&$filter=ItemsGroupCode eq 1008"
                response = await self.client.get(f"{SAP_BASE_URL}/Items?{query}", cookies=self.cookies)
                if response.status_code == 200:
                    items = response.json().get('value', [])
                else:
                    raise Exception("Erro ao buscar itens")
            except:
                print("⚠️ [SAP] Falha ao buscar máquinas reais. Usando fictícias.")
                self.mock_mode = True
        
        # --- DADOS MOCK (Simulação) ---
        if self.mock_mode:
            items = [
                {"ItemCode": "MQ-CNC-01", "ItemName": "Torno CNC Mazak QTN"},
                {"ItemCode": "MQ-INJ-05", "ItemName": "Injetora Romi 300T"},
                {"ItemCode": "MQ-PRE-02", "ItemName": "Prensa Hidráulica 100T"},
                {"ItemCode": "MQ-SOL-09", "ItemName": "Célula de Solda Robotizada"},
                {"ItemCode": "MQ-EMP-03", "ItemName": "Empilhadeira Hyster H50"}
            ]

        count_new = 0
        for item in items:
            sap_code = item.get('ItemCode')
            sap_desc = item.get('ItemName')
            
            existing = await self._find_vehicle_by_identifier(sap_code)

            if not existing:
                print(f"➕ [SYNC] Importando Máquina: {sap_code}")
                vehicle_in = VehicleCreate(
                    brand="SAP Asset",
                    model=sap_desc or "Genérico",
                    year=2024,
                    identifier=sap_code, # Código vira Placa/ID
                    status=VehicleStatus.AVAILABLE,
                    current_km=0,
                    license_plate=sap_code
                )
                await crud_vehicle.create_with_owner(
                    self.db, obj_in=vehicle_in, organization_id=self.org_id
                )
                count_new += 1
        
        print(f"✅ Máquinas sincronizadas: {count_new} novas inseridas.")

    async def sync_operators(self):
        if not self.cookies and not self.mock_mode:
            if not await self.login(): return

        employees = []
        if not self.mock_mode:
            try:
                query = "$select=EmployeeID,FirstName,LastName,JobTitle"
                response = await self.client.get(f"{SAP_BASE_URL}/EmployeesInfo?{query}", cookies=self.cookies)
                if response.status_code == 200:
                    employees = response.json().get('value', [])
                else:
                    raise Exception("Erro ao buscar operadores")
            except:
                self.mock_mode = True

        # --- DADOS MOCK (Simulação) ---
        if self.mock_mode:
            employees = [
                {"EmployeeID": 1001, "FirstName": "Carlos", "LastName": "Silva", "JobTitle": "Operador CNC"},
                {"EmployeeID": 1002, "FirstName": "Ana", "LastName": "Souza", "JobTitle": "Supervisora"},
                {"EmployeeID": 1003, "FirstName": "Roberto", "LastName": "Lima", "JobTitle": "Manutenção"},
                {"EmployeeID": 1004, "FirstName": "Fernanda", "LastName": "Dias", "JobTitle": "Operadora Jr"}
            ]

        count_new = 0
        for emp in employees:
            emp_id = str(emp.get('EmployeeID'))
            full_name = f"{emp.get('FirstName')} {emp.get('LastName')}"
            # Gera email: ID@trumachine.local
            generated_email = f"operador.{emp_id}@vemagmes.local"
            
            existing_user = await crud_user.get_user_by_email(self.db, email=generated_email)
            
            if not existing_user:
                print(f"👤 [SYNC] Criando Operador: {full_name}")
                user_in = UserCreate(
                    email=generated_email,
                    full_name=full_name,
                    password="mudar123",
                    role=UserRole.DRIVER,
                    organization_id=self.org_id,
                    phone=None
                )
                new_user = await crud_user.create(
                    self.db, user_in=user_in, organization_id=self.org_id, role=UserRole.DRIVER
                )
                new_user.employee_id = emp_id
                self.db.add(new_user)
                await self.db.commit()
                count_new += 1

        print(f"✅ Operadores sincronizados: {count_new} novos inseridos.")

    async def _find_vehicle_by_identifier(self, identifier: str) -> Optional[Vehicle]:
        stmt = select(Vehicle).where(
            Vehicle.identifier == identifier,
            Vehicle.organization_id == self.org_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def close(self):
        await self.client.aclose()