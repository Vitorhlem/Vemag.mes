import asyncio
import httpx
import json

# --- COLOQUE SEUS DADOS REAIS AQUI ---
SAP_URL = "https://192.168.0.XXX:50000/b1s/v1" # IP do seu servidor SAP
COMPANY_DB = "SUA_BASE"
USER = "SEU_USUARIO"
PASSWORD = "SUA_SENHA"

async def scan_campos_roteiro():
    # verify=False ignora erros de certificado SSL (comum em servidores locais)
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    
    try:
        print(f"🔐 [SAP] Conectando ao banco {COMPANY_DB}...")
        login_res = await client.post(
            f"{SAP_URL}/Login",
            json={"CompanyDB": COMPANY_DB, "UserName": USER, "Password": PASSWORD}
        )
        
        if login_res.status_code != 200:
            print(f"❌ Erro de Autenticação: {login_res.text}")
            return

        cookies = login_res.cookies
        print("✅ Autenticado com sucesso!")

        # 1. Buscamos a primeira O.P. disponível para analisar a estrutura
        print(f"🔍 [SAP] Lendo estrutura da tabela LGCROT...")
        # Pegamos o top 1 para ser rápido
        url = f"{SAP_URL}/LGCROT?$top=1"
        res = await client.get(url, cookies=cookies)

        if res.status_code == 200:
            data = res.json().get('value', [])
            if not data:
                print("⚠️  Nenhum roteiro encontrado no SAP para análise.")
                return

            header = data[0]
            # 2. Localiza a coleção de linhas (Geralmente LGLCROTCollection)
            # Procuramos qualquer chave que contenha 'LGLCROT'
            colecao_chave = next((k for k in header.keys() if "LGLCROT" in k), None)

            if not colecao_chave:
                print("❌ Não foi possível encontrar a coleção de linhas (LGLCROT) dentro do objeto.")
                print(f"Campos disponíveis no cabeçalho: {list(header.keys())}")
                return

            linhas = header.get(colecao_chave, [])
            if not linhas:
                print(f"⚠️  A coleção '{colecao_chave}' existe, mas esta O.P. não tem linhas.")
                return

            # 3. LISTAGEM DE TODOS OS CAMPOS DAS LINHAS
            print(f"\n🚀 [SUCESSO] Campos encontrados na tabela de linhas ({colecao_chave}):")
            print("-" * 50)
            
            primeira_linha = linhas[0]
            todos_os_campos = sorted(list(primeira_linha.keys()))
            
            for campo in todos_os_campos:
                valor_amostra = primeira_linha[campo]
                print(f"🔹 {campo} (Exemplo: {valor_amostra})")
            
            print("-" * 50)
            print(f"✅ Total de {len(todos_os_campos)} colunas identificadas.")

        else:
            print(f"❌ Erro na consulta (Status {res.status_code}): {res.text}")

    except Exception as e:
        print(f"💥 Erro fatal durante a execução: {str(e)}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(scan_campos_roteiro())