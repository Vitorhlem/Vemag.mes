from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class IERPAdapter(ABC):
    """
    Interface genérica para comunicação com sistemas ERP.
    Garante que o sistema TruMachine funcione com SAP, Totvs, ou Mock.
    """

    @abstractmethod
    async def get_item_details(self, item_code: str) -> Optional[Dict[str, Any]]:
        """Busca detalhes de um item/máquina pelo código."""
        pass

    @abstractmethod
    async def get_production_orders(self) -> List[Dict[str, Any]]:
        """Busca lista de OPs liberadas."""
        pass

    @abstractmethod
    async def get_order_details(self, op_code: str) -> Optional[Dict[str, Any]]:
        """Busca detalhes completos (cabeçalho + roteiro) de uma OP ou OS."""
        pass

    @abstractmethod
    async def send_appointment(self, payload: Dict[str, Any]) -> bool:
        """Envia apontamento de produção ou parada."""
        pass

    @abstractmethod
    async def get_open_service_orders(self) -> List[Dict[str, Any]]:
        """Busca ordens de serviço em aberto."""
        pass