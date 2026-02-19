import httpx
import asyncio
import urllib3
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Imports do Módulo CRUD e Models
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

    # Helper interno para verificar existência de veículo
    async def _find_vehicle_by_identifier(self, identifier: str) -> Optional[Vehicle]:
        query = select(Vehicle).where(Vehicle.identifier == identifier)
        result = await self.db.execute(query)
        return result.scalars().first()

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

                        # Truncar strings para evitar erro "value too long"
                        safe_model = sap_desc[:50]
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
                            await self.db.rollback()
                    else:
                        print(f"      ℹ️ Máquina já existe no banco.")
                else:
                    print(f"      ⚠️ Erro API SAP: {response.status_code}")

            except Exception as e:
                print(f"      ❌ Exceção ao processar {target_code}: {str(e)}")
                try:
                    await self.db.rollback()
                except:
                    pass

        print("🏁 [SAP] Sincronização de máquinas concluída.")

    # =========================================================================
    # 2. LISTAGEM DE OPs (LISTA GERAL)
    # =========================================================================
    async def get_released_production_orders(self) -> List[dict]:
        if not self.cookies:
            if not await self.login(): return []

        try:
            # 1. Busca as OPs Liberadas no SAP
            # [MODIFICADO] Adicionado U_LGO_DocEntryOPsFather (Sem underscore) para exibição visual
            fields = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,U_LGO_DocEntryOPsFather,U_Desenho"
            query = f"$select={fields}&$filter=ProductionOrderStatus eq 'boposReleased'&$orderby=DocumentNumber desc"            
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
                father_id = str(op.get('U_LGO_DocEntryOPsFather') or "")
                steps = []

                # 2. BUSCA O ROTEIRO NA ENGENHARIA (LGCROT)
                route_url = f"{SAP_BASE_URL}/LGCROT?$filter=Code eq '{item_code}'&$select=LGLCROTCollection"
                route_res = await self.client.get(route_url, cookies=self.cookies)
                
                if route_res.status_code == 200:
                    route_data = route_res.json().get('value', [])
                    
                    # Verifica se o roteiro existe e possui a coleção de linhas
                    if route_data and 'LGLCROTCollection' in route_data[0]:
                        collection = route_data[0]['LGLCROTCollection']
                        print(f"🔍 [DEBUG SAP] OP {op_id}: Processando {len(collection)} etapas...")
                        
                        for s in collection:
                            # ✅ CORREÇÃO: Captura a instrução específica desta linha/etapa
                            raw_instr = s.get('U_Instrucoes')
                            if raw_instr:
                                instr_formatada = str(raw_instr).replace('\r\n', '\n').replace('\r', '\n').strip()
                            else:
                                instr_formatada = f"Recurso: {s.get('U_CentroTra')}"
                                instr_formatada = str(raw_instr).strip() if raw_instr else "Consulte o desenho técnico para esta etapa."
                            
                            steps.append({
                                "seq": s.get('U_Posicao'),
                                "resource": s.get('U_Operacao'), 
                                "name": s.get('U_Descr'),      
                                "description": instr_formatada,  # ✅ AGORA VAI O TEXTO CERTO DA LINHA
                                "status": "PENDING",
                                "timeEst": float(s.get('U_TMMOPU') or 0)
                            })
                        print(f"✅ [LOG] OP {op_id}: {len(steps)} operações carregadas.")
                    else:
                        print(f"⚠️  [LOG] OP {op_id}: Roteiro '{item_code}' sem operações cadastradas.")
                else:
                    print(f"❌ [LOG] OP {op_id}: Falha ao acessar LGCROT (Status: {route_res.status_code}).")

                

                # 3. Montagem do objeto final para o Frontend
                cleaned_ops.append({
                    "op_number": op_id,
                    "item_code": item_code,
                    "part_name": op.get('ProductDescription'),
                    "planned_qty": op.get('PlannedQuantity'),
                    "uom": op.get('InventoryUOM'),
                    "type": "Standard",
                    "custom_ref": father_id,
                    "drawing": str(op.get('U_Desenho') or ""),
                    "steps": steps 
                })

            print(f"\n✨ [MES] Carga finalizada com sucesso.")
            return cleaned_ops

        except Exception as e:
            print(f"💥 [MES CRITICAL ERROR] {str(e)}")
            return []

    # =========================================================================
    # 3. BUSCA DE OP ÚNICA (ATUALIZADA COM ROTEIRO MESTRE)
    # =========================================================================
    async def get_production_order_by_code(self, op_code: str) -> Optional[dict]:
        if not self.cookies:
            if not await self.login(): return None

        # --- LÓGICA PARA ORDEM DE SERVIÇO (O.S.) ---
        if str(op_code).startswith("OS-"):
            try:
                # Formato esperado: OS-{DocNum}-{LineId} (Ex: OS-4595-1)
                parts = str(op_code).split('-')
                if len(parts) < 3: return None
                
                doc_num = parts[1]
                target_line_id = int(parts[2])

                print(f"🔄 [SAP] Buscando O.S. #{doc_num} (Linha {target_line_id})...")
                
                # Busca a O.S. específica pelo Número do Documento
                query = f"$select=DocEntry,DocNum,U_CardName,LGLDOS2Collection&$filter=DocNum eq {doc_num}"
                res = await self.client.get(f"{SAP_BASE_URL}/LGDOS?{query}", cookies=self.cookies)
                
                if res.status_code == 200:
                    data = res.json().get('value', [])
                    if data:
                        os_doc = data[0]
                        client_name = os_doc.get('U_CardName') or "Cliente"
                        
                        # Procura a linha correta dentro da coleção
                        for line in os_doc.get('LGLDOS2Collection', []):
                            if line.get('LineId') == target_line_id:
                                item_code = line.get('U_ItemCode')
                                item_name = line.get('U_ItemName') # O valor para U_DescricaoServico
                                roteiro_code = line.get('U_Roteiro') or item_code
                                
                                # Busca o roteiro dessa linha (igual fazemos na lista)
                                steps = []
                                if roteiro_code:
                                    rot_url = f"{SAP_BASE_URL}/LGCROT?$filter=Code eq '{roteiro_code}'&$select=LGLCROTCollection"
                                    rot_res = await self.client.get(rot_url, cookies=self.cookies)
                                    if rot_res.status_code == 200:
                                        rot_data = rot_res.json().get('value', [])
                                        if rot_data and 'LGLCROTCollection' in rot_data[0]:
                                            for s in rot_data[0]['LGLCROTCollection']:
                                                raw_instr = s.get('U_Instrucoes')
                                                instr = str(raw_instr).replace('\r\n', '\n').replace('\r', '\n').strip() if raw_instr else f"Recurso: {s.get('U_CentroTra')}"
                                                steps.append({
                                                    "seq": s.get('U_Posicao'),
                                                    "resource": s.get('U_Operacao'),
                                                    "name": s.get('U_Descr'),
                                                    "description": instr,
                                                    "status": "PENDING",
                                                    "timeEst": float(s.get('U_TMMOPU') or 0)
                                                })

                                # ✅ CORREÇÃO AQUI: Convertendo para float e garantindo o UOM
                                try:
                                    planned_qty_os = float(line.get('U_Qtde') or 0.0)
                                except (ValueError, TypeError):
                                    planned_qty_os = 0.0

                                print(f"✅ [SAP] O.S. encontrada: {item_name}")
                                return {
                                    "op_number": op_code,
                                    "status": "Released", 
                                    "item_code": item_code,
                                    "part_name": item_name, 
                                    "planned_qty": planned_qty_os, # <--- MUDANÇA AQUI
                                    "uom": "pç",   
                                    "is_service": True,                # <--- MUDANÇA AQUI (Padrão para OS)
                                    "custom_ref": f"Cliente: {client_name}",
                                    "type": "Service",
                                    "drawing": "",
                                    "steps": steps
                                }
                print(f"❌ [SAP] O.S. {op_code} não encontrada ou sem linha correspondente.")
                return None
            except Exception as e:
                print(f"❌ [SAP] Erro ao buscar O.S: {e}")
                return None

        # --- LÓGICA PARA ORDEM DE PRODUÇÃO (O.P.) ---
        clean_code = str(op_code).replace("OP-", "").strip()
        if not clean_code.isdigit(): return None

        try:
            # 1. BUSCA DADOS BÁSICOS DA O.P. 
            print(f"🔄 [SAP] Buscando Cabeçalho da OP {clean_code}...")
            fields_op = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,ProductionOrderStatus,U_LGO_DocEntryOPsFather,U_Desenho"
            query_op = f"$select={fields_op}&$filter=DocumentNumber eq {clean_code}"
            
            resp_op = await self.client.get(f"{SAP_BASE_URL}/ProductionOrders?{query_op}", cookies=self.cookies)
            
            if resp_op.status_code != 200:
                print(f"❌ [SAP] Erro ao buscar OP {clean_code}: {resp_op.status_code}")
                return None

            items = resp_op.json().get('value', [])
            if not items: return None
            
            op_data = items[0]
            item_code = op_data.get('ItemNo')
            
            print(f"✅ [SAP] OP Encontrada. Item: {item_code}. Buscando Roteiro de Engenharia (LGCROT)...")

            # 2. BUSCA O ROTEIRO NA TABELA MESTRE (LGCROT)
            query_rot = f"$select=Code,Name,LGLCROTCollection&$filter=Code eq '{item_code}'"
            resp_rot = await self.client.get(f"{SAP_BASE_URL}/LGCROT?{query_rot}", cookies=self.cookies)
            
            steps = []
            
            if resp_rot.status_code == 200:
                rot_items = resp_rot.json().get('value', [])
                if rot_items:
                    roteiro = rot_items[0]
                    etapas_raw = roteiro.get('LGLCROTCollection', [])
                    
                    for etapa in etapas_raw:
                        raw_instr = etapa.get('U_Instrucoes')
                        instr_formatada = str(raw_instr).strip() if raw_instr else f"Recurso: {etapa.get('U_CentroTra')}"
                        
                        try:
                            seq = int(etapa.get('U_Posicao', 0))
                        except:
                            seq = 0
                        
                        steps.append({
                            "seq": seq,
                            "resource": etapa.get('U_Operacao', ''),  
                            "name": etapa.get('U_Descr', 'Etapa sem nome'),
                            "description": instr_formatada,           
                            "timeEst": float(etapa.get('U_TMMOPU') or 0),
                            "status": "PENDING"
                        })
                    
                    steps.sort(key=lambda x: x['seq'])
                    print(f"✅ [SAP] Roteiro carregado com {len(steps)} etapas para a OP {clean_code}.")
                else:
                    print(f"⚠️ [SAP] Roteiro de Engenharia não encontrado para o item {item_code}.")
            else:
                print(f"❌ [SAP] Erro ao buscar LGCROT: {resp_rot.status_code}")

            # ✅ CORREÇÃO AQUI: Formatando valores com segurança antes de retornar
            try:
                planned_qty_op = float(op_data.get('PlannedQuantity') or 0.0)
            except (ValueError, TypeError):
                planned_qty_op = 0.0

            uom_op = op_data.get('InventoryUOM') or "pç"

            # 3. RETORNA O OBJETO COMPLETO PARA O FRONTEND
            return {
                "op_number": op_data.get('DocumentNumber'),
                "status": op_data.get('ProductionOrderStatus'),
                "item_code": item_code,
                "part_name": op_data.get('ProductDescription'),
                "planned_qty": planned_qty_op, # <--- MUDANÇA AQUI
                "uom": uom_op,                 # <--- MUDANÇA AQUI
                "custom_ref": op_data.get('U_LGO_DocEntryOPsFather') or "",
                "drawing": str(op_data.get('U_Desenho') or ""),
                "steps": steps
            }

        except Exception as e:
            print(f"❌ [SAP] Erro Crítico na busca por código: {e}")
            return None

    # =========================================================================
    # 4. APONTAMENTO DE PRODUÇÃO
    # =========================================================================
    async def create_production_appointment(self, appointment_data: dict, sap_resource_code: str) -> bool:
        if not self.cookies:
            if not await self.login(): return False

        # --- 1. DETECÇÃO DE CONTEXTO ---
        op_number_raw = str(appointment_data.get('op_number', ''))
        
        # Flag: É Ordem de Serviço? (Começa com OS- ou tem estrutura de OS)
        is_os = op_number_raw.startswith("OS-")
        
        # Flag: É Parada? (Tem motivo ou é Setup)
        is_stop_reason = bool(appointment_data.get('stop_reason'))
        is_setup_desc = "setup" in str(appointment_data.get('stop_description', '')).lower()
        is_stop = is_stop_reason or is_setup_desc

        # --- 2. TRATAMENTO DO NÚMERO DO DOCUMENTO ---
        # Se for OS (Ex: OS-4595-1), pega o meio (4595). Se for OP normal, mantém.
        if is_os and '-' in op_number_raw:
            try:
                final_doc_num = op_number_raw.split('-')[1]
            except:
                final_doc_num = op_number_raw
        else:
            final_doc_num = op_number_raw

        # --- 3. REGRAS DE NEGÓCIO (SAP FIELDS) ---
        
        # REGRA 1: Origem é SEMPRE "S"
        u_origem = "S"

        # REGRA 2: Tipo de Documento
        # Se for Parada OU O.S. -> Tipo 2
        # Se for Produção (OP) -> Tipo 1
        if is_stop or is_os:
            u_tipo_doc = "2"
        else:
            u_tipo_doc = "1"

        # REGRA 3: Serviço
        # Só preenche se for O.S. (pois o item_code vem do appointment_data)
        u_servico = str(appointment_data.get('item_code', '')) if is_os else ""

        # --- 4. DATAS E HORAS ---
        dt_ini = appointment_data.get('start_time')
        dt_fim = appointment_data.get('end_time')
        
        if isinstance(dt_ini, str): dt_ini = datetime.fromisoformat(dt_ini.replace('Z', '+00:00'))
        if isinstance(dt_fim, str): dt_fim = datetime.fromisoformat(dt_fim.replace('Z', '+00:00'))

        br_tz = timezone(timedelta(hours=-3))
        dt_ini_local = dt_ini.astimezone(br_tz) if dt_ini.tzinfo else dt_ini.replace(tzinfo=timezone.utc).astimezone(br_tz)
        dt_fim_local = dt_fim.astimezone(br_tz) if dt_fim.tzinfo else dt_fim.replace(tzinfo=timezone.utc).astimezone(br_tz)

        sap_data_ini = dt_ini_local.strftime("%Y-%m-%d")
        sap_data_fim = dt_fim_local.strftime("%Y-%m-%d")
        sap_hora_ini = int(dt_ini_local.strftime("%H%M"))
        sap_hora_fim = int(dt_fim_local.strftime("%H%M"))
        
        # Tratamento do Operador
        raw_id = str(appointment_data['operator_id']).strip().lstrip('0')
        sap_operator_id = raw_id[:-1] if len(raw_id) > 1 and raw_id.isdigit() else raw_id

        # Flag Setup e Apto Parada
        is_setup_val = "S" if is_setup_desc else "N"
        is_apto_parada = "S" if (is_stop_reason or is_setup_val == "S") else "N"

        # Limpeza de Campos se for Tipo 2 (Geralmente Tipo 2 ignora Operação/Posição se for parada)
        # Mas para O.S. (que agora é Tipo 2), talvez precise manter. 
        # Vou manter a lógica segura: Se for PARADA limpa, se for PROD/OS mantém.
        if is_stop:
            posicao_final = ""
            operacao_final = ""
        else:
            posicao_final = str(appointment_data.get('position', ''))
            operacao_final = str(appointment_data.get('operation', ''))

        payload = {
            "U_NumeroDocumento": final_doc_num,
            "U_Posicao": posicao_final,
            "U_Operacao": operacao_final,
            "U_DescricaoOperacao": appointment_data.get('operation_desc', ''),
            "U_DescricaoServico": appointment_data.get('part_description', ''), 
            "U_DescricaoOperador": appointment_data.get('operator_name', ''),
            "U_Recurso": str(appointment_data['resource_code']),        
            "U_DescricaoRecurso": str(appointment_data['resource_name']),
            "U_Operador": sap_operator_id,
            "U_DataInicioAp": sap_data_ini,
            "U_DataFimAp": sap_data_fim,
            "U_HoraInicioAp": sap_hora_ini,
            "DataSource": "I",
            "U_HoraFimAp": sap_hora_fim,
            "U_MotivoParada": appointment_data.get('stop_reason', ""),
            "U_DescricaoParada": appointment_data.get('stop_description', ""),
            "U_setup": is_setup_val,
            "U_AptoParada": is_apto_parada,
            "U_OrigemApontamento": u_origem,  # <--- AGORA SEMPRE "S"
            "U_TipoDocumento": u_tipo_doc,    # <--- 1 (OP) ou 2 (OS/Stop)
            "U_Servico": u_servico
        }

        try:
            print(f"🏭 [SAP] Payload ({'OS' if is_os else 'OP'}): {payload}")
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

    async def get_open_service_orders(self) -> List[dict]:
        if not self.cookies:
            if not await self.login(): return []

        try:
            # Busca O.S. com Status 'O' (Open) e suas linhas (@LGLDOS2)
            query = "$select=DocEntry,DocNum,U_CardName,LGLDOS2Collection&$filter=Status eq 'O'&$orderby=DocNum desc"
            print(f"\n🛠️ [MES] Buscando Ordens de Serviço (O.S.) abertas...")
            
            res = await self.client.get(f"{SAP_BASE_URL}/LGDOS?{query}", cookies=self.cookies)
            if res.status_code != 200:
                print(f"❌ [SAP] Erro ao buscar O.S: {res.status_code}")
                return []

            service_orders = []
            raw_data = res.json().get('value', [])

            for os in raw_data:
                doc_num = os.get('DocNum')
                client_name = os.get('U_CardName') or "Cliente Diversos"
                
                # Processa cada LINHA da O.S. como uma ordem selecionável
                for line in os.get('LGLDOS2Collection', []):
                    item_code = line.get('U_ItemCode')
                    item_name = line.get('U_ItemName') or "Serviço sem descrição"
                    qty = line.get('U_Qtde')
                    roteiro_code = line.get('U_Roteiro') or item_code # Fallback para o item se roteiro vazio
                    line_id = line.get('LineId')
                    line_status = line.get('U_Status') # Ou line.get('LineStatus')
                    if line_status in ['C', 'Fechado', 'Encerrado']:
                        continue

                    # Identificador único Híbrido: OS-{DocNum}-{LineId}
                    unique_op_id = f"OS-{doc_num}-{line_id}"
                    
                    # Busca o Roteiro na LGCROT (Igual à O.P.)
                    steps = []
                    if roteiro_code:
                        rot_url = f"{SAP_BASE_URL}/LGCROT?$filter=Code eq '{roteiro_code}'&$select=LGLCROTCollection"
                        rot_res = await self.client.get(rot_url, cookies=self.cookies)
                        
                        if rot_res.status_code == 200:
                            rot_data = rot_res.json().get('value', [])
                            if rot_data and 'LGLCROTCollection' in rot_data[0]:
                                for s in rot_data[0]['LGLCROTCollection']:
                                    raw_instr = s.get('U_Instrucoes')
                                    # Formatação do texto
                                    instr = str(raw_instr).replace('\r\n', '\n').replace('\r', '\n').strip() if raw_instr else f"Recurso: {s.get('U_CentroTra')}"
                                    
                                    steps.append({
                                        "seq": s.get('U_Posicao'),
                                        "resource": s.get('U_Operacao'),
                                        "name": s.get('U_Descr'),
                                        "description": instr,
                                        "status": "PENDING",
                                        "timeEst": float(s.get('U_TMMOPU') or 0)
                                    })

                    # Adiciona à lista final
                    service_orders.append({
                        "op_number": unique_op_id,  # O Front vai ver "OS-4595-1"
                        "item_code": item_code,     # Importante para o U_Servico
                        "part_name": f"[OS] {item_name}",
                        "planned_qty": qty,
                        "uom": "UN",
                        "type": "Service",          
                        "is_service": True,         # ✅ NOVA FLAG ADICIONADA AQUI
                        "custom_ref": f"Cliente: {client_name}",
                        "drawing": "",
                        "steps": steps
                    })

            print(f"✅ [MES] {len(service_orders)} itens de serviço carregados.")
            return service_orders

        except Exception as e:
            print(f"💥 [MES ERROR] Falha ao buscar O.S: {str(e)}")
            return []