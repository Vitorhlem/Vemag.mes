# src-py/main.py
import io
import os
import shutil
import sys
from PIL import Image

# ======================= AUTO-ENV CREATION =======================
env_path = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_path):
    print("⚠️  Arquivo .env não encontrado. Iniciando criação automática...")
    if "development" in sys.argv:
        source_file = ".env.development"
        print("🚀  Modo DEVELOPMENT detectado.")
    else:
        source_file = ".env.example"
        print("ℹ️  Nenhum modo específico detectado. Usando padrão (.env.example).")
    
    source_path = os.path.join(os.path.dirname(__file__), source_file)
    if os.path.exists(source_path):
        shutil.copy(source_path, env_path)
        print(f"✅  Arquivo .env criado com sucesso a partir de {source_file}!")
    else:
        print(f"❌  Erro: Arquivo fonte {source_file} não encontrado.")
# =================================================================

from fastapi import FastAPI, Request, status, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError, HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select # 👈 Importado para buscar a org da máquina

# Importações da sua aplicação
from app.api import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import engine, async_session # 👈 Importado async_session
from app.core.websocket_manager import manager 

# ======================= BLOCO DE IMPORTAÇÃO DOS MODELOS =======================
from app.db.base_class import Base
from app.models.organization_model import Organization
from app.models.user_model import User
from app.models.machine_model import Machine
from app.models.tool_model import Tool
from app.models.part_model import Part, InventoryItem 
from app.models.maintenance_model import MaintenanceRequest, MaintenanceComment
from app.models.notification_model import Notification
from app.models.inventory_transaction_model import InventoryTransaction
from app.models.document_model import Document
from app.models.machine_component_model import MachineComponent
from app.models.feedback_model import Feedback
from app.routers import drawings
# ==============================================================================

setup_logging()
UPLOAD_DIR = "static/uploads"

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

os.makedirs(UPLOAD_DIR, exist_ok=True)

# 5. Configurar o CORS
origins_list = []
if settings.BACKEND_CORS_ORIGINS:
    origins_list.extend([str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS])

manual_origins = [
    "http://localhost",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "http://localhost:3000",
    "http://192.168.0.5:9500",
    "http://192.168.0.5:9000",
    "http://192.168.0.5:8080", 
    "http://192.168.0.5",
    "https://trumachine.netlify.app",
    "http://192.168.0.5:8000/docs",
    "capacitor://localhost",
    "http://localhost:8000"
]
origins_list.extend(manual_origins)
origins_list = list(set(origins_list))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"] 
)

# ======================= ROTA WEBSOCKET (CORRIGIDA) =======================
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """
    Endpoint Global de WebSocket (Rodando no main.py).
    Resolve automaticamente o ID da Organização para agrupar as conexões.
    """
    # Lógica para definir a qual Organização este socket pertence
    org_id = 1 # Fallback padrão (Organização Principal)

    if client_id > 90000:
        # Se for o ID alto (99xxx) do Painel do Gestor, conecta na Org 1
        # Isso permite que o dashboard receba os alertas gerais.
        org_id = 1
    else:
        # Se for um ID baixo, provavelmente é uma Máquina se conectando.
        # Vamos ao banco descobrir qual é a organização dela.
        async with async_session() as db:
            try:
                # Busca apenas o organization_id da máquina para ser rápido
                result = await db.execute(select(Machine.organization_id).where(Machine.id == client_id))
                found_org = result.scalars().first()
                if found_org:
                    org_id = found_org
            except Exception as e:
                print(f"⚠️ Erro ao resolver Org para cliente {client_id}: {e}")

    # 🚀 CORREÇÃO: Agora passamos o org_id corretamente!
    await manager.connect(websocket, org_id=org_id)
    
    try:
        while True:
            # Mantém a conexão viva
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        # 🚀 CORREÇÃO: Passamos o org_id também na desconexão
        manager.disconnect(websocket, org_id=org_id)
        
    except Exception as e:
        print(f"Erro no WebSocket {client_id}: {e}")
# =========================================================================

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    custom_errors = []
    for err in errors:
        new_err = err.copy()
        if 'input' in new_err and isinstance(new_err['input'], bytes):
            new_err['input'] = "Binary data"
        if err['type'] == 'enum':
            allowed_values = err['ctx'].get('expected', 'valores permitidos')
            new_err['msg'] = f"O valor deve ser um dos seguintes: {allowed_values}"
        custom_errors.append(new_err)
    return JSONResponse(status_code=422, content={"detail": custom_errors})

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 413:
        return JSONResponse(status_code=413, content={"detail": "Arquivo muito grande (Máx 5MB)."})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Arquivo não é uma imagem.")
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        img.verify()
        
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{os.urandom(8).hex()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
            
        return JSONResponse(content={"file_url": f"/static/uploads/{unique_filename}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {e}")

@app.get("/", status_code=200, include_in_schema=False)
def read_root():
    return {"status": f"Welcome to {settings.PROJECT_NAME} API!"}

app.include_router(api_router, prefix=settings.API_V1_STR)

# 👇 ADICIONE ESTA LINHA AQUI 👇
app.include_router(drawings.router, prefix=settings.API_V1_STR)