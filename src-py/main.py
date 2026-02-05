# backend/main.py
import io
import os
import shutil
import sys
from PIL import Image

# ======================= AUTO-ENV CREATION =======================
# Verifica se o arquivo .env existe. Se não, cria uma cópia baseada
# nos argumentos ou no padrão.
env_path = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_path):
    print("⚠️  Arquivo .env não encontrado. Iniciando criação automática...")
    
    # Verifica se o argumento 'development' foi passado
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
        print(f"❌  Erro: Arquivo fonte {source_file} não encontrado. Não foi possível criar o .env.")
# =================================================================

from fastapi import FastAPI, Request, status, UploadFile, File, HTTPException
from fastapi.exceptions import RequestValidationError, HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Importações da sua aplicação
from app.api import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import engine

# ======================= BLOCO DE IMPORTAÇÃO DOS MODELOS =======================
# Este bloco garante que a Base do SQLAlchemy conheça todas as suas tabelas
# antes que a função on_startup seja chamada para criá-las.

from app.db.base_class import Base
from app.models.organization_model import Organization
from app.models.user_model import User
from app.models.vehicle_model import Vehicle
from app.models.implement_model import Implement
# Nota: InventoryItem está definido dentro de part_model.py
from app.models.part_model import Part, InventoryItem 
from app.models.client_model import Client
from app.models.freight_order_model import FreightOrder
from app.models.stop_point_model import StopPoint
from app.models.journey_model import Journey
from app.models.maintenance_model import MaintenanceRequest, MaintenanceComment
from app.models.fuel_log_model import FuelLog
from app.models.notification_model import Notification
from app.models.location_history_model import LocationHistory
from app.models.achievement_model import Achievement, UserAchievement
from app.models.inventory_transaction_model import InventoryTransaction
from app.models.document_model import Document
from app.models.goal_model import Goal
from app.models.alert_model import Alert
from app.models.vehicle_cost_model import VehicleCost
from app.models.vehicle_component_model import VehicleComponent
from app.models.tire_model import VehicleTire
from app.models.fine_model import Fine
from app.models.feedback_model import Feedback
from app.models.demo_usage_model import DemoUsage
from app.routers import drawings
# ==============================================================================


# 1. Configurar o logging primeiro
setup_logging()

# 2. Definir constantes
UPLOAD_DIR = "static/uploads"

# 3. Criar a instância principal da aplicação
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 4. Criar diretórios necessários
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 5. Configurar o CORS (Híbrido: Settings + Manuais)
origins_list = []

# Adiciona origens do arquivo .env (se houver)
if settings.BACKEND_CORS_ORIGINS:
    origins_list.extend([str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS])

# Adiciona origens manuais necessárias (Local, Rede, Netlify)
manual_origins = [
    "http://localhost",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "http://localhost:3000",
    "http://192.168.0.22:9500", # Acesso via rede local
    "http://192.168.0.22:9000",
    "http://192.168.0.22",
    "http://192.168.15.8:9000", # Acesso via rede local alternativa
    "https://trumachine.netlify.app", # Seu front no Netlify
    "https://trumachine.netlify.app/"
]
origins_list.extend(manual_origins)

# Remove duplicatas para limpar o log
origins_list = list(set(origins_list))

print(f"🔓  CORS Permitidos: {origins_list}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. Adicionar o evento de startup para criar as tabelas
@app.on_event("startup")
async def on_startup():
    """
    Cria as tabelas no banco de dados na inicialização da aplicação.
    """
    async with engine.begin() as conn:
        # Agora, Base.metadata.create_all conhece todas as tabelas importadas acima
        await conn.run_sync(Base.metadata.create_all)

# 7. Adicionar Handlers de Exceção
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    custom_errors = []
    for err in errors:
        new_err = err.copy()
        
        # Correção para upload de arquivos: remove o input binário do log de erro
        if 'input' in new_err and isinstance(new_err['input'], bytes):
            new_err['input'] = "Binary data (files or multipart form)"
            
        if err['type'] == 'enum':
            allowed_values = err['ctx'].get('expected', 'valores permitidos')
            new_err['msg'] = f"O valor deve ser um dos seguintes: {allowed_values}"
        
        custom_errors.append(new_err)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": custom_errors},
    )

# 8. Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 413:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Arquivo muito grande. O limite máximo é de 5MB."},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# 9. Endpoint de Upload
@app.post("/upload-photo")
async def upload_photo(file: UploadFile = File(..., max_size=5 * 1024 * 1024)): # Limite de 5MB
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="O arquivo não é uma imagem válida.")

    # --- Validação de conteúdo com Pillow ---
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        img.verify() 
    except Exception:
        raise HTTPException(status_code=400, detail="Falha ao processar. O arquivo pode estar corrompido ou não é uma imagem válida.")
    # --- Fim da validação ---

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{os.urandom(8).hex()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a imagem: {e}")

    file_url = f"/static/uploads/{unique_filename}"
    return JSONResponse(content={"file_url": file_url})

# 10. Adicionar a rota raiz para verificação de status
@app.get("/", status_code=200, include_in_schema=False)
def read_root():
    return {"status": f"Welcome to {settings.PROJECT_NAME} API!"}

# 11. Incluir o roteador principal da API
app.include_router(api_router, prefix=settings.API_V1_STR)