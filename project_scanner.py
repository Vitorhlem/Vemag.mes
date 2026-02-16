import os
import re
import sys
from collections import defaultdict

# Forçar encoding UTF-8 na saída padrão para evitar erros no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Configurações
IGNORE_DIRS = {'node_modules', '.git', '__pycache__', 'venv', 'dist', '.idea', '.vscode'}
EXTENSIONS_PY = {'.py'}
EXTENSIONS_JS = {'.ts', '.vue', '.js'}

# Estruturas de dados
definitions = defaultdict(list)  # { 'NomeClasse': ['path/file.py'] }
file_imports = defaultdict(set)  # { 'path/file.py': {'NomeClasse', 'OutraCoisa'} }
files_scanned = []

def should_ignore(path):
    parts = path.split(os.sep)
    return any(p in IGNORE_DIRS for p in parts)

def find_definitions_py(content, file_path):
    # Encontra classes e tabelas SQLAlchemy
    classes = re.findall(r'class\s+(\w+)', content)
    tables = re.findall(r'__tablename__\s*=\s*[\'"](\w+)[\'"]', content)
    
    for c in classes:
        definitions[c].append(file_path)
    for t in tables:
        definitions[f"Table:{t}"].append(file_path)

def find_definitions_js(content, file_path):
    # Encontra classes exportadas, interfaces e nomes de componentes Vue
    exports = re.findall(r'export\s+(?:class|interface|type|const)\s+(\w+)', content)
    
    # Tenta pegar o nome do componente Vue
    if file_path.endswith('.vue'):
        file_name = os.path.basename(file_path).replace('.vue', '')
        definitions[file_name].append(file_path)

    for e in exports:
        definitions[e].append(file_path)

def scan_project(root_dir):
    print(f"[INFO] Iniciando analise em: {root_dir} ...")
    
    for root, _, files in os.walk(root_dir):
        if should_ignore(root):
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            
            if ext not in EXTENSIONS_PY and ext not in EXTENSIONS_JS:
                continue

            files_scanned.append(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # 1. Registrar Definições (O que este arquivo CRIA)
                    if ext in EXTENSIONS_PY:
                        find_definitions_py(content, file_path)
                    elif ext in EXTENSIONS_JS:
                        find_definitions_js(content, file_path)
                    
                    # 2. Registrar Usos (O que este arquivo USA)
                    # Uma busca simples de texto por palavras inteiras
                    words = set(re.findall(r'\b\w+\b', content))
                    file_imports[file_path] = words
                    
            except Exception as e:
                print(f"[ERRO] ao ler {file_path}: {e}")

def generate_report():
    print("\n" + "="*50)
    print("RELATORIO DE ANALISE DO PROJETO VEMAG.MES")
    print("="*50)
    
    unused_definitions = []

    # 1. Verificar arquivos "Órfãos"
    print(f"\n[FILES] Arquivos Escaneados: {len(files_scanned)}")
    print(f"[DEFS] Definicoes Encontradas: {len(definitions)}")

    print("\n[ALERT] --- POSSIVEIS CODIGOS MORTOS (Nao encontrados em outros arquivos) ---")
    for name, locations in definitions.items():
        if len(name) < 4: continue 
        
        usage_count = 0
        for f_path, words in file_imports.items():
            if f_path not in locations and name in words:
                usage_count += 1
        
        if usage_count == 0:
            if "main" in locations[0] or "endpoint" in locations[0] or "routes" in locations[0]:
                continue
            print(f"  [X] '{name}' definido em {locations[0]} (Zero referencias encontradas)")
            unused_definitions.append(name)

    print("\n[LINK] --- ANALISE DE MODELS (Backend -> Frontend) ---")
    py_models = [k for k, v in definitions.items() if 'src-py' in v[0] and not k.startswith('Table:')]
    
    for model in py_models:
        found_in_client = False
        for f_path, words in file_imports.items():
            if 'src-client' in f_path and model in words:
                print(f"  [OK] Model '{model}' usado no Frontend em: {os.path.basename(f_path)}")
                found_in_client = True
                break
        
        if not found_in_client:
             print(f"  [WARN] Model '{model}' NAO encontrado explicitamente no Frontend (Verifique DTOs)")

if __name__ == "__main__":
    current_dir = os.getcwd()
    try:
        scan_project(current_dir)
        generate_report()
    except Exception as e:
        print(f"Erro fatal: {e}")