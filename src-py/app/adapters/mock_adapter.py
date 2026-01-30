from typing import List, Optional, Dict, Any
from app.adapters.erp_interface import IERPAdapter
import json

class MockAdapter(IERPAdapter):
    """
    Adaptador de Simulação (Mock) para desenvolvimento local e testes.
    Retorna dados estáticos sem conectar a nenhum ERP.
    """

    async def get_item_details(self, item_code: str) -> Optional[Dict[str, Any]]:
        # Simula a busca de uma máquina ou item
        return {
            "ItemCode": item_code, 
            "ItemName": f"MÁQUINA MOCK {item_code}",
            "ItemsGroupCode": 100,
            "Valid": "Y"
        }

    async def get_production_orders(self) -> List[Dict[str, Any]]:
        # Simula lista de OPs liberadas
        return [
            {
                "op_number": "4152", 
                "item_code": "MOCK-EIXO-01", 
                "part_name": "EIXO TESTE MOCK",
                "planned_qty": 100.0, 
                "uom": "PC", 
                "custom_ref": "4152/0", 
                "drawing": "",
                "type": "Standard", 
                "steps": [
                    {"seq": 10, "resource": "4.02.01", "name": "SETUP", "timeEst": 1.0, "status": "PENDING"},
                    {"seq": 20, "resource": "4.02.01", "name": "USINAGEM", "timeEst": 5.0, "status": "PENDING"}
                ]
            },
            {
                "op_number": "4153", 
                "item_code": "MOCK-TAMPA-02", 
                "part_name": "TAMPA DE PROTEÇÃO",
                "planned_qty": 50.0, 
                "uom": "PC", 
                "custom_ref": "4153/0", 
                "drawing": "",
                "type": "Standard", 
                "steps": []
            }
        ]

    async def get_order_details(self, op_code: str) -> Optional[Dict[str, Any]]:
        print(f"⚠️ [MOCK] Detalhes OP: {op_code}")
        
        # Simula resposta para O.S.
        if str(op_code).startswith("OS-"):
            return {
                "op_number": op_code,
                "status": "Released",
                "item_code": "SERV-001",
                "part_name": "SERVIÇO DE MANUTENÇÃO MOCK",
                "planned_qty": 1.0,
                "uom": "UN",
                "custom_ref": "Cliente Mock Ltda",
                "type": "Service",
                "drawing": "",
                "steps": [
                    {"seq": 10, "resource": "Geral", "name": "Execução Serviço", "timeEst": 4.0, "status": "PENDING"}
                ]
            }

        # Simula resposta para O.P.
        return {
            "op_number": op_code, 
            "status": "boposReleased",
            "item_code": "MOCK-EIXO-01",
            "part_name": f"PEÇA MOCK ({op_code})", 
            "planned_qty": 100.0,
            "uom": "PC",
            "custom_ref": f"{op_code}/0",
            "drawing": "",
            "type": "Standard",
            "steps": [
                {"seq": 10, "resource": "4.02.01", "name": "SETUP MOCK", "timeEst": 1.0, "status": "PENDING"},
                {"seq": 20, "resource": "4.02.01", "name": "USINAGEM MOCK", "timeEst": 2.0, "status": "PENDING"}
            ]
        }

    async def send_appointment(self, payload: Dict[str, Any]) -> bool:
        print(f"⚠️ [MOCK SEND] Payload Recebido: {json.dumps(payload, default=str)}")
        return True

    async def get_open_service_orders(self) -> List[Dict[str, Any]]:
        # CORREÇÃO AQUI: Adicionados todos os campos obrigatórios
        return [
            {
                "op_number": "OS-999-1",
                "item_code": "SRV-MOCK-001",   # <-- Adicionado
                "part_name": "SERVIÇO MOCK",
                "planned_qty": 10.0,           # <-- Adicionado
                "uom": "UN",                   # <-- Adicionado
                "custom_ref": "Cliente Mock",  # <-- Adicionado
                "type": "Service",             # <-- Adicionado
                "drawing": "",                 # <-- Adicionado
                "steps": []                    # <-- Adicionado
            },
            {
                "op_number": "OS-888-2",
                "item_code": "SRV-REPARO-02",
                "part_name": "REPARO HIDRÁULICO",
                "planned_qty": 1.0,
                "uom": "SER",
                "custom_ref": "Oficina Central",
                "type": "Service",
                "drawing": "",
                "steps": []
            }
        ]