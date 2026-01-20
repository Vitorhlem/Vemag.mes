import httpx
import asyncio
import urllib3

# Desabilita avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIG ---
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

# Nome da Tabela (COM O ARROBA) para buscar nos metadados
TABLE_NAME = "@LGO_CAPONTAMENTO"

async def check_fields():
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        print(f"🕵️ Conectando para inspecionar {TABLE_NAME}...")
        
        # 1. Login
        resp = await client.post(f"{SAP_BASE_URL}/Login", json={
            "CompanyDB": SAP_COMPANY_DB, "UserName": SAP_USER, "Password": SAP_PASSWORD
        })
        
        if resp.status_code != 200:
            print(f"❌ Erro de Login: {resp.text}")
            return

        cookies = resp.cookies
        print("✅ Login OK! Buscando estrutura da tabela...")

        # 2. Busca nos Metadados de Campos de Usuário
        # O SAP guarda as definições dos campos na tabela 'UserFieldsMD'
        query = f"$filter=TableName eq '{TABLE_NAME}'&$select=Name,Description,Type,SubType"
        
        try:
            r = await client.get(f"{SAP_BASE_URL}/UserFieldsMD?{query}", cookies=cookies)
            data = r.json()
            
            fields = data.get('value', [])
            
            if not fields:
                print(f"⚠️ Nenhum campo encontrado para a tabela {TABLE_NAME}. Verifique se o nome da tabela está correto (tem que ter o @).")
            else:
                print("\n📋 CAMPOS ENCONTRADOS NO SAP:")
                print("=" * 80)
                print(f"{'NOME NO JSON (Use este!)':<30} | {'DESCRIÇÃO (Tela)':<30} | {'TIPO'}")
                print("=" * 80)
                
                # Campos padrão que sempre existem (mas não estão no UserFieldsMD)
                print(f"{'Code':<30} | {'Código Primário':<30} |String")
                print(f"{'Name':<30} | {'Nome/Descrição':<30} |String")
                print("-" * 80)

                for f in fields:
                    # O nome no JSON sempre começa com U_
                    json_name = f"U_{f['Name']}"
                    desc = f['Description']
                    print(f"{json_name:<30} | {desc:<30} | {f['Type']}")
                
                print("=" * 80)
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_fields())