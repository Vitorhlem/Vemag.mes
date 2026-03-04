from fastapi import APIRouter

# Importamos todos os endpoints de uma só vez para melhor organização
from app.v1.endpoints import (
    admin,
    dashboard,
    tools,
    login,
    maintenance,
    notifications,
    performance,
    report_generator,
    users,
    machines,
    documents,
    machine_costs,
    settings,
    utils,
    parts,
    machine_components,
    costs,
    integrations,
    feedback,
    audit_logs,
    alerts,
    production,
    andon,
    
)

api_router = APIRouter()

# Registamos cada router com o seu prefixo e tag
api_router.include_router(login.router, prefix="/login", tags=["Login"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Panel"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(machines.router, prefix="/machines", tags=["Machines"])
api_router.include_router(machine_costs.router, prefix="/machines/{machine_id}/costs", tags=["Machine Costs"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])
api_router.include_router(report_generator.router, prefix="/report-generator", tags=["Report Generator"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(utils.router, prefix="/utils", tags=["Utilities"])
api_router.include_router(parts.router, prefix="/parts", tags=["Parts"]) 
api_router.include_router(machine_components.router, tags=["Machine Components"])
api_router.include_router(costs.router, prefix="/costs", tags=["Costs"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(production.router, prefix="/production", tags=["production"])
api_router.include_router(andon.router, prefix="/andon", tags=["Andon System"])
api_router.add_api_route("/upload-photo", utils.upload_photo, methods=["POST"], tags=["Utilities"])
