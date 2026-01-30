from app.core.config import settings
from app.adapters.erp_interface import IERPAdapter
from app.adapters.sap_adapter import SapB1Adapter
from app.adapters.mock_adapter import MockAdapter

def get_erp_adapter() -> IERPAdapter:
    if settings.SAP_USE_MOCK:
        return MockAdapter()
    return SapB1Adapter()