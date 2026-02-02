from app.db.base_class import Base

# 1. Organização e Usuários
from .organization_model import Organization, Sector
from .user_model import User, UserRole

# 2. Ativos e Jornada
from .vehicle_model import Vehicle, VehicleStatus
from .journey_model import Journey
from .implement_model import Implement
from .fine_model import Fine

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
    VehicleDailyMetric
)

# 5. Logística e Clientes
from .client_model import Client
from .freight_order_model import FreightOrder
from .stop_point_model import StopPoint

# 6. Operacional e Custos
from .fuel_log_model import FuelLog
from .vehicle_cost_model import VehicleCost, CostType
from .notification_model import Notification
from .location_history_model import LocationHistory

# 7. Estoque e Peças
from .part_model import Part, PartCategory
from .inventory_transaction_model import InventoryTransaction

# 8. Engajamento e Gamificação
from .achievement_model import Achievement, UserAchievement

# 9. Andon e Alertas
from .andon_model import AndonCall
from .alert_model import Alert

# 10. Auditoria (ADICIONADO)
from .audit_log_model import AuditLog