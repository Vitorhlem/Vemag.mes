# backend/app/crud/__init__.py

from . import crud_user as user
from . import crud_organization as organization
from . import crud_machine as machine
from . import crud_part as part
from . import crud_inventory_transaction as inventory_transaction
from . import crud_machine_cost as machine_cost
from . import crud_machine_component as machine_component
from . import crud_maintenance as maintenance
from . import crud_maintenance_comment as maintenance_comment
from . import crud_document as document
from . import crud_tool as tool
from . import crud_notification as notification
from .crud_production import production 