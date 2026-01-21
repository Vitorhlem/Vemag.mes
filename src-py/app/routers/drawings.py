# Arquivo: src-py/app/routers/drawings.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import json
import glob
from pypdf import PdfReader  # Biblioteca para ler o texto do PDF

router = APIRouter(prefix="/drawings", tags=["Drawings"])

# Configurações de Pastas
DRAWINGS_DIR = os.path.join(os.getcwd(), "static", "drawings")
MAP_FILE = os.path.join(DRAWINGS_DIR, "drawing_map.json")

def load_mapping():
    """Carrega o mapa de cache existente."""
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_mapping(new_map):
    """Salva o novo aprendizado no arquivo JSON."""
    try:
        with open(MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_map, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar mapa: {e}")

def scan_pdf_for_text(filepath, search_text):
    """
    Abre o PDF e verifica se o 'search_text' (código da peça) 
    está escrito em algum lugar da primeira página.
    """
    try:
        reader = PdfReader(filepath)
        # Geralmente o código está na primeira página (legenda)
        if len(reader.pages) > 0:
            text = reader.pages[0].extract_text()
            # Remove espaços em branco extras e quebras de linha para facilitar a busca
            clean_text = text.replace('\n', '').replace(' ', '')
            clean_search = search_text.replace(' ', '') # Remove espaços do código buscado (ex: BJ 075 -> BJ075)
            
            if clean_search in clean_text:
                return True
    except Exception as e:
        print(f"Erro ao ler arquivo {filepath}: {e}")
    return False

@router.get("/{item_code}")
async def get_drawing(item_code: str):
    """
    Busca Inteligente de Desenho:
    1. Tenta pelo nome do arquivo.
    2. Tenta pelo cache (map.json).
    3. Tenta LER o conteúdo dos arquivos PDF na pasta.
    """
    
    target_code = item_code.strip()
    if not os.path.exists(DRAWINGS_DIR):
        os.makedirs(DRAWINGS_DIR)

    # --- TENTATIVA 1: O nome do arquivo já é o código? (Mais rápido) ---
    safe_code = target_code.replace("/", "-")
    direct_match = glob.glob(os.path.join(DRAWINGS_DIR, f"*{safe_code}*.pdf"))
    if direct_match:
        # Pega o mais recente
        best_file = max(direct_match, key=os.path.getmtime)
        return FileResponse(best_file)

    # --- TENTATIVA 2: Já aprendemos esse arquivo antes? (Cache) ---
    mapping = load_mapping()
    if target_code in mapping:
        filename = mapping[target_code]
        file_path = os.path.join(DRAWINGS_DIR, filename)
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            # Se o arquivo sumiu, remove do mapa
            del mapping[target_code]

    # --- TENTATIVA 3: SCANNER PROFUNDO (Lê dentro dos arquivos) ---
    print(f"Iniciando busca profunda por: {target_code}...")
    
    # Lista todos os PDFs da pasta
    all_pdfs = glob.glob(os.path.join(DRAWINGS_DIR, "*.pdf"))
    
    for pdf_path in all_pdfs:
        filename = os.path.basename(pdf_path)
        
        # Pula arquivos que já sabemos que são de OUTRAS peças (Otimização)
        if filename in mapping.values():
            continue

        # Verifica se o código está escrito dentro do PDF
        if scan_pdf_for_text(pdf_path, target_code):
            print(f"ENCONTRADO! O código {target_code} está no arquivo {filename}")
            
            # Sucesso! Salva no mapa para não precisar ler de novo amanhã
            mapping[target_code] = filename
            save_mapping(mapping)
            
            return FileResponse(pdf_path)

    # Se chegou aqui, não achou em lugar nenhum
    raise HTTPException(status_code=404, detail="Desenho não encontrado. Verifique se o código da peça consta na legenda do PDF.")