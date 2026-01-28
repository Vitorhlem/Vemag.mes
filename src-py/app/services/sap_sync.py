import httpx
import asyncio
import urllib3
from typing import List, Optional
from datetime import timedelta, datetime
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

        # Lista completa de máquinas alvo
        target_machines = [
            "AT000337", "AT000338", "AT000339", "AT000340", "AT000341",
            "AT000237", "AT000238", "AT000205", "AT000212", "AT000214",
            "AT000239", "AT000293", "AT000155", "AT000242", "AT000241",
            "CP000115", "AT000005", "AT000007", "AT000008", "AT000963",
            "AT001314", "AT000912"
        ]

        print(f"🎯 [SAP] Iniciando sincronização de {len(target_machines)} máquinas...")

        for target_code in target_machines:
            print(f"   🔄 Buscando item: {target_code}...")
            
            query = f"$select=ItemCode,ItemName,ItemsGroupCode,Valid&$filter=ItemCode eq '{target_code}'"
            
            try:
                response = await self.client.get(f"{SAP_BASE_URL}/Items?{query}", cookies=self.cookies)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('value', [])
                    
                    if not items:
                        print(f"      ❌ Item {target_code} não encontrado no SAP.")
                        continue

                    item = items[0]
                    sap_code = item.get('ItemCode')
                    sap_desc = item.get('ItemName') or "Sem Descrição"
                    
                    # Verifica se veículo já existe no banco local
                    existing = await self._find_vehicle_by_identifier(sap_code)
                    
                    if not existing:
                        print(f"      ➕ Cadastrando {sap_code}...")
                        
                        # Inferência de Marca
                        brand = "GENERICA"
                        if "ROMI" in sap_desc.upper(): brand = "ROMI"
                        elif "NARDINI" in sap_desc.upper(): brand = "NARDINI"
                        elif "TITAN" in sap_desc.upper(): brand = "TITAN"
                        elif "ZOCCA" in sap_desc.upper(): brand = "ZOCCA"
                        elif "NEWAY" in sap_desc.upper(): brand = "NEWAY"
                        elif "STANKPORT" in sap_desc.upper(): brand = "STANKPORT"
                        elif "FRANHO" in sap_desc.upper(): brand = "FRANHO"

                        # [CORREÇÃO] Truncar strings para evitar erro "value too long for type varchar(50)"
                        safe_model = sap_desc[:50] # Corta nos primeiros 50 caracteres
                        safe_brand = brand[:50]

                        vehicle_in = VehicleCreate(
                            brand=safe_brand, 
                            model=safe_model, 
                            year=datetime.now().year, 
                            identifier=sap_code,
                            status=VehicleStatus.AVAILABLE, 
                            current_km=0, 
                            license_plate=sap_code,
                            sap_resource_code=""
                        )
                        
                        try:
                            await crud_vehicle.create_with_owner(self.db, obj_in=vehicle_in, organization_id=self.org_id)
                            print(f"      ✅ Sucesso!")
                        except Exception as e:
                            print(f"      ❌ Erro ao salvar no banco: {e}")
                            # [IMPORTANTE] Rollback para não travar a próxima iteração
                            await self.db.rollback()
                    else:
                        print(f"      ℹ️ Máquina já existe no banco.")
                else:
                    print(f"      ⚠️ Erro API SAP: {response.status_code}")

            except Exception as e:
                print(f"      ❌ Exceção ao processar {target_code}: {str(e)}")
                # Garante rollback se o erro foi de banco de dados
                try:
                    await self.db.rollback()
                except:
                    pass

        print("🏁 [SAP] Sincronização de máquinas concluída.")

    # =========================================================================
    # 2. LISTAGEM DE OPs
    # =========================================================================
    async def get_released_production_orders(self) -> List[dict]:
        if not self.cookies:
            if not await self.login(): return []

        try:
            # 1. Busca as OPs Liberadas
            fields = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,U_LGO_DocEntryOPsFather,U_Desenho"
            query = f"$select={fields}&$filter=ProductionOrderStatus eq 'boposReleased'&$top=20&$orderby=DocumentNumber desc"
            
            print(f"\n🚀 [MES] Iniciando carga de OPs e Roteiros B1Plus...")
            response = await self.client.get(f"{SAP_BASE_URL}/ProductionOrders?{query}", cookies=self.cookies)
            
            if response.status_code != 200:
                print(f"❌ [SAP] Erro ao buscar OPs: {response.status_code}")
                return []

            ops_raw = response.json().get('value', [])
            cleaned_ops = []

            for op in ops_raw:
                op_id = op.get('DocumentNumber')
                item_code = op.get('ItemNo')
                steps = []

                # 2. BUSCA O ROTEIRO NA ENGENHARIA (LGCROT)
                route_url = f"{SAP_BASE_URL}/LGCROT?$filter=Code eq '{item_code}'&$select=LGLCROTCollection"
                route_res = await self.client.get(route_url, cookies=self.cookies)
                
                if route_res.status_code == 200:
                    routes = route_res.json().get('value', [])
                    if routes and routes[0].get('LGLCROTCollection'):
                        raw_steps = routes[0]['LGLCROTCollection']
                        
                        for s in raw_steps:
                            # --- NOVO: Cálculo de tempo para satisfazer o Pydantic ---
                            # Somamos Setup + Máquina + Mão de Obra
                            total_time = (
                                float(s.get('U_TempoSet') or 0) + 
                                float(s.get('U_TempoMaq') or 0) + 
                                float(s.get('U_TempoMO') or 0)
                            )

                            steps.append({
                                "seq": s.get('U_Posicao') or str(s.get('LineId')),
                                "resource": s.get('U_Operacao') or "",
                                "name": s.get('U_Descr') or "Operação sem nome",
                                "description": f"Centro de Trabalho: {s.get('U_CentroTra')}",
                                "status": "PENDING",
                                "timeEst": total_time  # <--- FIX: Agora o campo obrigatório existe!
                            })
                        print(f"✅ [LOG] OP {op_id}: {len(steps)} operações carregadas.")
                    else:
                        print(f"⚠️  [LOG] OP {op_id}: Roteiro '{item_code}' sem operações.")
                else:
                    print(f"❌ [LOG] OP {op_id}: Falha LGCROT ({route_res.status_code}).")

                # 3. Montagem do objeto final
                cleaned_ops.append({
                    "op_number": op_id,
                    "item_code": item_code,
                    "part_name": op.get('ProductDescription'),
                    "planned_qty": op.get('PlannedQuantity'),
                    "uom": op.get('InventoryUOM'),
                    "type": "Standard",
                    "custom_ref": str(op.get('U_LGO_DocEntryOPsFather') or ""),
                    "drawing": str(op.get('U_Desenho') or ""),
                    "steps": steps 
                })

            print(f"\n✨ [MES] Carga finalizada com sucesso.")
            return cleaned_ops

        except Exception as e:
            print(f"💥 [MES CRITICAL ERROR] {str(e)}")
            return []

   
    # =========================================================================
    # 3. BUSCA DE OP ÚNICA
    # =========================================================================
    async def get_production_order_by_code(self, op_code: str) -> Optional[dict]:
        if not self.cookies:
            if not await self.login(): return None

        clean_code = str(op_code).replace("OP-", "").strip()
        if not clean_code.isdigit(): return None

        try:
            fields = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,ProductionOrderStatus,U_LGO_DocEntryOPsFather,ProductionOrderLines"
            query = f"$select={fields}&$filter=DocumentNumber eq {clean_code}"
            
            print(f"🔄 [SAP] Buscando OP {clean_code} e Roteiro...")
            response = await self.client.get(f"{SAP_BASE_URL}/ProductionOrders?{query}", cookies=self.cookies)
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                if items:
                    item = items[0]
                    steps = []
                    raw_lines = item.get('ProductionOrderLines', [])
                    
                    for line in raw_lines:
                        item_code = line.get('ItemCode') or ""
                        seq_num = line.get('VisualOrder', 0) * 10
                        
                        steps.append({
                            "seq": seq_num,
                            "resource": item_code,
                            "name": line.get('ItemName') or "Etapa de Produção",
                            "description": f"Operação SAP: {item_code} - {line.get('ItemName')}",
                            "timeEst": line.get('PlannedQuantity') or 0,
                            "status": "PENDING"
                        })
                    
                    steps.sort(key=lambda x: x['seq'])

                    return {
                        "op_number": item.get('DocumentNumber'),
                        "status": item.get('ProductionOrderStatus'),
                        "item_code": item.get('ItemNo'),
                        "part_name": item.get('ProductDescription'),
                        "planned_qty": item.get('PlannedQuantity'),
                        "uom": item.get('InventoryUOM'),
                        "custom_ref": item.get('U_LGO_DocEntryOPsFather') or "",
                        "steps": steps
                    }
            return None
        except Exception as e:
            print(f"❌ [SAP] Erro Busca OP Única: {e}")
            return None
        
    async def _find_vehicle_by_identifier(self, identifier: str) -> Optional[Vehicle]:
        stmt = select(Vehicle).where(
            Vehicle.identifier == identifier, 
            Vehicle.organization_id == self.org_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    # =========================================================================
    # 4. APONTAMENTO DE PRODUÇÃO
    # =========================================================================
    async def create_production_appointment(self, appointment_data: dict, sap_resource_code: str) -> bool:
        if not self.cookies:
            if not await self.login(): return False

        dt_ini = appointment_data['start_time']
        dt_fim = appointment_data['end_time']

        if dt_ini.tzinfo: dt_ini_local = dt_ini
        else: dt_ini_local = dt_ini - timedelta(hours=3)
            
        if dt_fim.tzinfo: dt_fim_local = dt_fim
        else: dt_fim_local = dt_fim - timedelta(hours=3)

        sap_data_ini = dt_ini_local.strftime("%Y-%m-%d")
        sap_data_fim = dt_fim_local.strftime("%Y-%m-%d")
        sap_hora_ini = int(dt_ini_local.strftime("%H%M"))
        sap_hora_fim = int(dt_fim_local.strftime("%H%M"))

        raw_id = str(appointment_data['operator_id']).strip().lstrip('0')
        sap_operator_id = raw_id[:-1] if len(raw_id) > 1 else raw_id
        
        is_setup_val = "N"
        full_text = (str(appointment_data.get('stop_description', '')) + " " + 
                     str(appointment_data.get('operation_desc', '')) + " " +
                     str(appointment_data.get('stop_reason', ''))).lower()
        
        if "setup" in full_text or "prepara" in full_text: is_setup_val = "S"

        stop_reason = appointment_data.get('stop_reason', "")
        is_apto_parada = "S" if (stop_reason or is_setup_val == "S") else "N"

        payload = {
            "U_NumeroDocumento": str(appointment_data['op_number']),
            "U_Posicao": str(appointment_data['position']),
            "U_Operacao": str(appointment_data['operation']),
            "U_DescricaoOperacao": appointment_data.get('operation_desc', ''),
            "U_DescricaoServico": appointment_data.get('part_description', ''), 
            "U_DescricaoOperador": appointment_data.get('operator_name', ''),
            "U_Recurso": str(appointment_data['resource_code']),        
            "U_DescricaoRecurso": str(appointment_data['resource_name']),
            "U_Operador": sap_operator_id,
            "U_DataInicioAp": sap_data_ini,
            "U_DataFimAp": sap_data_fim,
            "U_HoraInicioAp": sap_hora_ini,
            "U_HoraFimAp": sap_hora_fim,
            "U_MotivoParada": appointment_data.get('stop_reason', ""),
            "U_DescricaoParada": appointment_data.get('stop_description', ""),
            "U_setup": is_setup_val,
            "U_TipoDocumento": "1",
            "U_AptoParada": is_apto_parada
        }
        try:
            print(f"🏭 [SAP] Enviando Apontamento... Payload: {payload}")
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