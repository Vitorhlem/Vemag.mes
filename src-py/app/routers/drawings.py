from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.core.celery_app import celery_app

router = APIRouter(prefix="/drawings", tags=["Drawings"])

CACHE_DIR = os.path.join(os.getcwd(), "static", "drawings_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# 1. Rota que o tablet chama para ACORDAR o Celery
@router.post("/request/{drawing_code}/{machine_id}")
async def request_drawing(drawing_code: str, machine_id: int):
    # Envia a ordem pro Celery rodar em background e libera o servidor na hora!
    celery_app.send_task("task_process_drawing", args=[drawing_code, machine_id])
    return {"status": "Processamento iniciado em background"}

# 2. Rota para o tablet baixar a imagem final
@router.get("/render/{filename}")
async def render_drawing(filename: str):
    file_path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Imagem não encontrada no cache.")