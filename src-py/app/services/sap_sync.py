import httpx
import asyncio
import urllib3
from typing import List, Optional
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Imports do Módulo CRUD
from app.crud import crud_vehicle
from app.schemas.vehicle_schema import VehicleCreate, VehicleStatus
from app.models.vehicle_model import Vehicle

# Desabilita avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIGURAÇÕES DO SAP
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

class SAPIntegrationService:
    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.org_id = organization_id
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)
        self.cookies = None

    async def login(self) -> bool:
        payload = {"CompanyDB": SAP_COMPANY_DB, "UserName": SAP_USER, "Password": SAP_PASSWORD}
        try:
            print(f"🔐 [SAP] Autenticando...")
            response = await self.client.post(f"{SAP_BASE_URL}/Login", json=payload)
            if response.status_code == 200:
                self.cookies = response.cookies
                print("✅ [SAP] Login OK.")
                return True
            else:
                print(f"⚠️ [SAP] Falha Login: {response.text}")
                return False 
        except Exception as e:
            print(f"❌ [SAP] Erro Conexão: {str(e)}")
            return False

    # =========================================================================
    # 1. SINCRONIZAÇÃO DE MÁQUINAS
    # =========================================================================
    async def sync_machines(self):
        if not self.cookies:
            if not await self.login(): return

        target_code = "AT000007"
        print(f"🎯 [SAP] Buscando item específico: {target_code}...")
        
        query = f"$select=ItemCode,ItemName,ItemsGroupCode,Valid&$filter=ItemCode eq '{target_code}'"
        
        try:
            response = await self.client.get(f"{SAP_BASE_URL}/Items?{query}", cookies=self.cookies)
            if response.status_code == 200:
                data = response.json()
                items = data.get('value', [])
                if not items:
                    print(f"❌ [SAP] Item {target_code} não encontrado.")
                    return

                item = items[0]
                sap_code = item.get('ItemCode')
                sap_desc = item.get('ItemName')
                
                existing = await self._find_vehicle_by_identifier(sap_code)
                if not existing:
                    print(f"➕ [SYNC] Cadastrando {sap_code}...")
                    vehicle_in = VehicleCreate(
                        brand="NARDINI", model=sap_desc, year=2024, identifier=sap_code,
                        status=VehicleStatus.AVAILABLE, current_km=0, license_plate=sap_code, sap_resource_code=""
                    )
                    await crud_vehicle.create_with_owner(self.db, obj_in=vehicle_in, organization_id=self.org_id)
                    print(f"✅ [SYNC] Sucesso!")
                else:
                    print(f"Info: Máquina já existe.")
            else:
                print(f"❌ [SAP] Erro busca máquinas: {response.text}")

        except Exception as e:
            print(f"❌ [SAP] Erro sync máquinas: {str(e)}")

    # =========================================================================
    # 2. LISTAGEM DE OPs (CORRIGIDO COM NOMES REAIS)
    # =========================================================================
    async def get_released_production_orders(self) -> List[dict]:
        if not self.cookies:
            if not await self.login(): return []

        try:
            # CORREÇÃO: Usando DocumentNumber, ItemNo, ProductDescription, PlannedQuantity
            fields = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,ProductionOrderStatus,U_LGO_DocEntryOPsFather,U_Desenho"
            
            # Filtro por 'boposReleased'
            query = f"$select={fields}&$filter=ProductionOrderStatus eq 'boposReleased'"
            
            print("🔄 [SAP] Buscando lista de OPs Liberadas...")
            response = await self.client.get(f"{SAP_BASE_URL}/ProductionOrders?{query}", cookies=self.cookies)
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                cleaned = []
                
                for item in items:
                    cleaned.append({
                        # Mapeamento com os novos nomes
                        "op_number": item.get('DocumentNumber'),
                        "item_code": item.get('ItemNo'),
                        "part_name": item.get('ProductDescription'),
                        "planned_qty": item.get('PlannedQuantity'),
                        "uom": item.get('InventoryUOM'),
                        "type": "Standard",
                        "custom_ref": item.get('U_LGO_DocEntryOPsFather') or "",
                        "drawing": item.get('U_Desenho') or ""
                    })
                
                print(f"📦 [SAP] Sucesso! {len(cleaned)} OPs liberadas encontradas.")
                return cleaned
            else:
                print(f"❌ [SAP] Erro ao buscar OPs: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"❌ [SAP] Exceção na listagem de OPs: {e}")
            return []

    # =========================================================================
    # 3. BUSCA DE OP ÚNICA (CORRIGIDO)
    # =========================================================================
    async def get_production_order_by_code(self, op_code: str) -> Optional[dict]:
        if not self.cookies:
            if not await self.login(): return None

        clean_code = str(op_code).replace("OP-", "").strip()
        if not clean_code.isdigit(): return None

        try:
            # CORREÇÃO: Incluímos 'ProductionOrderLines' na query para pegar o roteiro
            fields = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,ProductionOrderStatus,U_LGO_DocEntryOPsFather,ProductionOrderLines"
            
            query = f"$select={fields}&$filter=DocumentNumber eq {clean_code}"
            
            print(f"🔄 [SAP] Buscando OP {clean_code} e Roteiro...")
            response = await self.client.get(f"{SAP_BASE_URL}/ProductionOrders?{query}", cookies=self.cookies)
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                if items:
                    item = items[0]
                    
                    # --- EXTRAÇÃO DO ROTEIRO (STEPS) ---
                    steps = []
                    raw_lines = item.get('ProductionOrderLines', [])
                    
                    for line in raw_lines:
                        # No SAP, ItemType 290 geralmente é Recurso, 4 é Item. 
                        # Vamos pegar tudo que tiver um código válido de recurso.
                        line_type = line.get('ItemType') 
                        item_code = line.get('ItemCode') or ""
                        
                        # Formata a sequencia visual (ex: 1 -> 010)
                        seq_num = line.get('VisualOrder', 0) * 10
                        
                        step = {
                            "seq": seq_num,
                            "resource": item_code, # O "match" será feito com este código (Ex: 4.10)
                            "name": line.get('ItemName') or "Etapa de Produção",
                            "description": f"Operação SAP: {item_code} - {line.get('ItemName')}",
                            "timeEst": line.get('PlannedQuantity') or 0, # Tempo Planejado
                            "status": "PENDING"
                        }
                        steps.append(step)
                    
                    # Ordena pelo sequencial
                    steps.sort(key=lambda x: x['seq'])

                    return {
                        "op_number": item.get('DocumentNumber'),
                        "status": item.get('ProductionOrderStatus'),
                        "item_code": item.get('ItemNo'),
                        "part_name": item.get('ProductDescription'),
                        "quantity": item.get('PlannedQuantity'),
                        "uom": item.get('InventoryUOM'),
                        "custom_name": item.get('U_LGO_DocEntryOPsFather') or "",
                        "steps": steps # <--- Campo novo retornado
                    }
            return None
        except Exception as e:
            print(f"❌ [SAP] Erro Busca OP Única: {e}")
            return None

    # =========================================================================
    # 4. APONTAMENTO DE PRODUÇÃO
    # =========================================================================
    async def create_production_appointment(self, appointment_data: dict, sap_resource_code: str) -> bool:
        if not self.cookies:
            if not await self.login(): return False

        dt_ini = appointment_data['start_time']
        dt_fim = appointment_data['end_time']

        dt_ini_local = dt_ini - timedelta(hours=3)
        dt_fim_local = dt_fim - timedelta(hours=3)

        sap_data_ini = dt_ini_local.strftime("%Y-%m-%d")
        sap_data_fim = dt_fim_local.strftime("%Y-%m-%d")
        sap_hora_ini = int(dt_ini_local.strftime("%H%M"))
        sap_hora_fim = int(dt_fim_local.strftime("%H%M"))

        raw_id = str(appointment_data['operator_id']).strip().lstrip('0')
        sap_operator_id = raw_id[:-1] if len(raw_id) > 1 else raw_id
        final_resource = sap_resource_code if sap_resource_code else "4.02.01"

        payload = {
            "U_NumeroDocumento": str(appointment_data['op_number']),
            "U_Servico": "",
            "U_Posicao": str(appointment_data['position']),
            
            # --- CORREÇÃO: PREENCHIMENTO DA OPERAÇÃO ---
            "U_Operacao": str(appointment_data['operation']), # Agora recebe o código (ex: "701")
            "U_DescricaoOperacao": appointment_data.get('operation_desc', ''), # Novo campo SAP
            "U_DescricaoServico": appointment_data.get('part_description', ''), 
            
            # Frontend manda 'operator_name' -> SAP espera 'U_DescricaoOperador'
            "U_DescricaoOperador": appointment_data.get('operator_name', ''),
            "U_Recurso": final_resource,
            "U_Operador": sap_operator_id,
            
            "U_DataInicioAp": sap_data_ini,
            "U_DataFimAp": sap_data_fim,
            "U_HoraInicioAp": sap_hora_ini,
            "U_HoraFimAp": sap_hora_fim,
            "U_MotivoParada": appointment_data.get('stop_reason', "")
        }

        try:
            print(f"🏭 [SAP] Enviando Apontamento... Dados: {payload}")
            
            target_url = f"{SAP_BASE_URL}/LGO_CAPONTAMENTO"
            response = await self.client.post(target_url, json=payload, cookies=self.cookies)
            
            if response.status_code == 201:
                print(f"✅ [SAP] Sucesso! Code: {response.json().get('Code')}")
                return True
            else:
                print(f"❌ [SAP] Erro {response.status_code}: {response.text}")
                return False

        except Exception as e:
            print(f"❌ [SAP] Erro de envio: {str(e)}")
            return False