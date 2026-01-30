import httpx
import urllib3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.adapters.erp_interface import IERPAdapter

# Desabilita avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SapB1Adapter(IERPAdapter):
    def __init__(self):
        self.base_url = settings.SAP_API_URL
        self.company_db = settings.SAP_COMPANY_DB
        self.user = settings.SAP_USER
        self.password = settings.SAP_PASSWORD
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)
        self.cookies = None

    async def _login(self) -> bool:
        """Realiza o login no SAP Service Layer."""
        if settings.SAP_USE_MOCK:
            return True
            
        payload = {
            "CompanyDB": self.company_db, 
            "UserName": self.user, 
            "Password": self.password
        }
        try:
            # print(f"🔐 [SAP ADAPTER] Autenticando...")
            response = await self.client.post(f"{self.base_url}/Login", json=payload)
            if response.status_code == 200:
                self.cookies = response.cookies
                return True
            else:
                print(f"⚠️ [SAP] Falha Login: {response.text}")
                return False 
        except Exception as e:
            print(f"❌ [SAP] Erro Conexão: {str(e)}")
            return False

    async def _fetch_routing(self, item_code: str) -> List[Dict]:
        """
        Helper privado para buscar o roteiro de produção ou serviço (LGCROT).
        """
        if not item_code: return []
        
        try:
            url = f"{self.base_url}/LGCROT?$filter=Code eq '{item_code}'&$select=LGLCROTCollection"
            res = await self.client.get(url, cookies=self.cookies)
            
            steps = []
            if res.status_code == 200:
                data = res.json().get('value', [])
                if data and 'LGLCROTCollection' in data[0]:
                    for s in data[0]['LGLCROTCollection']:
                        # Captura instrução e formata
                        raw_instr = s.get('U_Instrucoes')
                        if raw_instr:
                            instr_formatada = str(raw_instr).replace('\r\n', '\n').replace('\r', '\n').strip()
                        else:
                            instr_formatada = f"Recurso: {s.get('U_CentroTra')}"

                        steps.append({
                            "seq": s.get('U_Posicao'),
                            "resource": s.get('U_Operacao'), 
                            "name": s.get('U_Descr'),      
                            "description": instr_formatada,
                            "status": "PENDING",
                            "timeEst": float(s.get('U_TempoMaq') or 0)
                        })
            
            # Ordena por sequência
            steps.sort(key=lambda x: int(x['seq']) if x['seq'] else 0)
            return steps
        except Exception as e:
            print(f"⚠️ [SAP] Erro ao buscar roteiro para {item_code}: {e}")
            return []

    async def get_item_details(self, item_code: str) -> Optional[Dict[str, Any]]:
        """Busca detalhes de um item (usado para importar máquinas)."""
        if not self.cookies and not await self._login(): return None
        
        query = f"$select=ItemCode,ItemName,ItemsGroupCode,Valid&$filter=ItemCode eq '{item_code}'"
        try:
            response = await self.client.get(f"{self.base_url}/Items?{query}", cookies=self.cookies)
            if response.status_code == 200:
                data = response.json().get('value', [])
                return data[0] if data else None
        except Exception as e:
            print(f"❌ [SAP] Erro ao buscar item {item_code}: {e}")
        return None

    async def get_production_orders(self) -> List[Dict[str, Any]]:
        """Busca todas as Ordens de Produção liberadas."""
        if not self.cookies and not await self._login(): return []

        try:
            fields = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,U_LGO_DocEntryOPsFather,U_Desenho"
            query = f"$select={fields}&$filter=ProductionOrderStatus eq 'boposReleased'&$top=20&$orderby=DocumentNumber desc"
            
            print(f"\n🚀 [SAP ADAPTER] Buscando OPs liberadas...")
            response = await self.client.get(f"{self.base_url}/ProductionOrders?{query}", cookies=self.cookies)
            
            if response.status_code != 200:
                print(f"❌ [SAP] Erro OPs: {response.status_code}")
                return []

            ops_raw = response.json().get('value', [])
            cleaned_ops = []

            for op in ops_raw:
                op_id = op.get('DocumentNumber')
                item_code = op.get('ItemNo')
                
                # Busca Roteiro usando o helper
                steps = await self._fetch_routing(item_code)

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
            
            return cleaned_ops

        except Exception as e:
            print(f"💥 [SAP CRITICAL] Erro listagem OPs: {e}")
            return []

    async def get_order_details(self, op_code: str) -> Optional[Dict[str, Any]]:
        """
        Busca detalhes completos de uma ordem.
        Identifica automaticamente se é O.S. (OS-...) ou O.P. (número).
        """
        if not self.cookies and not await self._login(): return None

        print(f"🔍 [SAP ADAPTER] Buscando detalhes: '{op_code}'")

        # =========================================================================
        # 1. LÓGICA DE ORDEM DE SERVIÇO (O.S.)
        # =========================================================================
        if str(op_code).startswith("OS-"):
            try:
                # Formato esperado: OS-{DocNum}-{LineId}
                parts = str(op_code).split('-')
                if len(parts) < 3: 
                    print("⚠️ [SAP] Formato de O.S. inválido.")
                    return None
                
                doc_num = parts[1]
                target_line_id = int(parts[2])

                # Busca a O.S. específica
                query = f"$select=DocEntry,DocNum,U_CardName,LGLDOS2Collection&$filter=DocNum eq {doc_num}"
                res = await self.client.get(f"{self.base_url}/LGDOS?{query}", cookies=self.cookies)
                
                if res.status_code == 200:
                    data = res.json().get('value', [])
                    if data:
                        os_doc = data[0]
                        client_name = os_doc.get('U_CardName') or "Cliente"
                        
                        # Procura a linha correta dentro da coleção
                        for line in os_doc.get('LGLDOS2Collection', []):
                            if line.get('LineId') == target_line_id:
                                item_code = line.get('U_ItemCode')
                                item_name = line.get('U_ItemName') 
                                roteiro_code = line.get('U_Roteiro') or item_code
                                
                                # Busca o roteiro dessa linha
                                steps = await self._fetch_routing(roteiro_code)

                                print(f"✅ [SAP] O.S. encontrada: {item_name}")
                                return {
                                    "op_number": op_code,
                                    "status": "Released", 
                                    "item_code": item_code,
                                    "part_name": item_name, 
                                    "planned_qty": line.get('U_Qtde'),
                                    "uom": "UN",
                                    "custom_ref": f"Cliente: {client_name}",
                                    "type": "Service",
                                    "drawing": "",
                                    "steps": steps
                                }
                print(f"❌ [SAP] O.S. {op_code} não encontrada.")
                return None
            except Exception as e:
                print(f"❌ [SAP] Erro ao buscar O.S: {e}")
                return None

        # =========================================================================
        # 2. LÓGICA DE ORDEM DE PRODUÇÃO (O.P.)
        # =========================================================================
        clean_code = str(op_code).replace("OP-", "").strip()
        if not clean_code.isdigit(): 
            print(f"❌ [SAP] Código inválido para O.P: {op_code}")
            return None

        try:
            fields_op = "DocumentNumber,ItemNo,ProductDescription,PlannedQuantity,InventoryUOM,ProductionOrderStatus,U_LGO_DocEntryOPsFather,U_Desenho"
            query_op = f"$select={fields_op}&$filter=DocumentNumber eq {clean_code}"
            
            resp_op = await self.client.get(f"{self.base_url}/ProductionOrders?{query_op}", cookies=self.cookies)
            
            if resp_op.status_code != 200: return None

            items = resp_op.json().get('value', [])
            if not items: return None
            
            op_data = items[0]
            item_code = op_data.get('ItemNo')
            
            # Busca roteiro
            steps = await self._fetch_routing(item_code)
            
            return {
                "op_number": op_data.get('DocumentNumber'),
                "status": op_data.get('ProductionOrderStatus'),
                "item_code": item_code,
                "part_name": op_data.get('ProductDescription'),
                "planned_qty": op_data.get('PlannedQuantity'), 
                "uom": op_data.get('InventoryUOM'),
                "custom_ref": op_data.get('U_LGO_DocEntryOPsFather') or "",
                "drawing": str(op_data.get('U_Desenho') or ""),
                "type": "Standard",
                "steps": steps
            }
        except Exception as e:
            print(f"💥 [SAP] Erro busca OP única: {e}")
            return None

    async def send_appointment(self, payload: Dict[str, Any]) -> bool:
        """Envia apontamento de produção ou parada para o SAP."""
        if not self.cookies and not await self._login(): return False
        
        # --- TRATAMENTO DE DADOS ---
        op_number_raw = str(payload.get('op_number', '')).strip()
        is_os = op_number_raw.startswith("OS-")
        is_stop = bool(payload.get('stop_reason'))
        
        final_doc_num = op_number_raw
        if is_os and '-' in op_number_raw:
            try: final_doc_num = op_number_raw.split('-')[1]
            except: pass
            
        # Validação de Segurança
        if not all(c.isdigit() or c == '/' for c in final_doc_num):
            if not (is_stop and final_doc_num == ""):
                print(f"⚠️ [SAP] DocNum inválido: {final_doc_num}")
                return False

        # --- FUSO HORÁRIO BRASIL ---
        br_zone = timezone(timedelta(hours=-3))
        def to_brasilia(dt):
            if isinstance(dt, str): 
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            
            if dt.tzinfo:
                return dt.astimezone(br_zone)
            else:
                return dt.replace(tzinfo=timezone.utc).astimezone(br_zone)

        dt_ini = to_brasilia(payload['start_time'])
        dt_fim = to_brasilia(payload['end_time'])
        
        # Lógica de Flags Setup/Parada
        stop_desc = str(payload.get('stop_description', '')).lower()
        is_setup = "S" if "setup" in stop_desc else "N"
        is_apto = "S" if (payload.get('stop_reason') or is_setup == "S") else "N"

        # Montagem do Payload SAP
        sap_payload = {
            "U_NumeroDocumento": final_doc_num, 
            "U_Posicao": str(payload.get('position', '')),
            "U_Operacao": str(payload.get('operation', '')),
            "U_DescricaoOperacao": payload.get('operation_desc', ''),
            "U_DescricaoServico": payload.get('part_description', ''), 
            "U_DescricaoOperador": payload.get('operator_name', ''),
            "U_Recurso": str(payload.get('resource_code', '')),        
            "U_DescricaoRecurso": str(payload.get('resource_name', '')),
            "U_Operador": str(payload.get('operator_id', '')).strip().lstrip('0'),
            "U_DataInicioAp": dt_ini.strftime("%Y-%m-%d"),
            "U_DataFimAp": dt_fim.strftime("%Y-%m-%d"),
            "U_HoraInicioAp": int(dt_ini.strftime("%H%M")),
            "U_HoraFimAp": int(dt_fim.strftime("%H%M")),
            "U_MotivoParada": payload.get('stop_reason', ""),
            "U_DescricaoParada": payload.get('stop_description', ""),
            "U_setup": is_setup,
            "U_AptoParada": is_apto,
            "U_OrigemApontamento": "S",
            "U_TipoDocumento": "2" if (is_os or is_stop) else "1",
            "U_Servico": payload.get('service_code', '') or (payload.get('item_code', '') if is_os else "")
        }

        try:
            print(f"📦 [SAP SEND] Enviando apontamento...")
            # print(json.dumps(sap_payload, indent=2)) # Debug opcional
            
            target_url = f"{self.base_url}/LGO_CAPONTAMENTO"
            resp = await self.client.post(target_url, json=sap_payload, cookies=self.cookies)
            
            if resp.status_code == 201:
                print(f"✅ [SAP] Sucesso: {resp.json().get('Code')}")
                return True
            else:
                print(f"❌ [SAP] Erro {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            print(f"❌ [SAP] Exceção envio: {e}")
            return False

    async def get_open_service_orders(self) -> List[Dict[str, Any]]:
        """Busca O.S. (LGDOS) com status aberto."""
        if not self.cookies and not await self._login(): return []

        try:
            query = "$select=DocEntry,DocNum,U_CardName,LGLDOS2Collection&$filter=Status eq 'O'"
            print(f"\n🛠️ [SAP ADAPTER] Buscando O.S. abertas...")
            
            res = await self.client.get(f"{self.base_url}/LGDOS?{query}", cookies=self.cookies)
            if res.status_code != 200:
                print(f"❌ [SAP] Erro busca O.S: {res.status_code}")
                return []
            
            orders = []
            for os in res.json().get('value', []):
                doc_num = os.get('DocNum')
                client = os.get('U_CardName') or "Cliente"
                
                for line in os.get('LGLDOS2Collection', []):
                    item = line.get('U_ItemCode')
                    item_name = line.get('U_ItemName')
                    line_id = line.get('LineId')
                    
                    # Busca Roteiro para esta linha
                    steps = await self._fetch_routing(line.get('U_Roteiro') or item)
                    
                    orders.append({
                        "op_number": f"OS-{doc_num}-{line_id}",
                        "item_code": item,
                        "part_name": item_name,
                        "planned_qty": line.get('U_Qtde'),
                        "uom": "UN",
                        "type": "Service",
                        "custom_ref": f"Cliente: {client}",
                        "drawing": "",
                        "steps": steps
                    })
            
            print(f"✅ [SAP] {len(orders)} O.S. encontradas.")
            return orders
        except Exception as e:
            print(f"💥 [SAP] Erro ao listar O.S: {e}")
            return []