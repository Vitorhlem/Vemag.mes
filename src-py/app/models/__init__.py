from app.db.base_class import Base

# 1. Organização e Usuários
from .organization_model import Organization, Sector
from .user_model import User, UserRole
from .feedback_model import Feedback 

# 2. Ativos e Jornada
from .machine_model import Machine, MachineStatus
from .tool_model import Tool
from .document_model import Document, DocumentType

# 3. Manutenção Industrial
from .maintenance_model import (
    MaintenanceRequest, 
    MaintenanceComment, 
    MaintenanceStatus, 
    MaintenanceCategory,
    MaintenancePartChange,
    MaintenanceServiceItem
)

# 4. Produção e MES (Consolidado)
from .production_model import (
    ProductionOrder, 
    ProductionLog, 
    ProductionSession, 
    ProductionTimeSlice,
    ProductionAppointment,
    EmployeeDailyMetric,
    MachineDailyMetric
)

# 6. Operacional e Custos
from .machine_cost_model import MachineCost, CostType
from .notification_model import Notification

# 7. Estoque e Peças
from .part_model import Part, PartCategory
from .inventory_transaction_model import InventoryTransaction

# 9. Andon e Alertas
from .andon_model import AndonCall

# 10 Auditoria
from .audit_log_model import AuditLog