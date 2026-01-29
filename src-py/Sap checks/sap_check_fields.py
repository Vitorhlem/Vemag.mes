import httpx
import asyncio
import urllib3

# Desabilita avisos de SSL (necessário para self-signed certificates do SAP)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES (Verifique se a senha/usuário estão atuais) ---
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"  # <-- Confirme se essa é a senha atual

# Nome da Tabela com o @ (UDT - User Defined Table)
TABLE_NAME = "@LGO_CAPONTAMENTO"

async def list_all_table_fields():
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        print(f"🕵️  Conectando ao SAP Service Layer para inspecionar {TABLE_NAME}...")
        
        # 1. Login
        login_payload = {
            "CompanyDB": SAP_COMPANY_DB, 
            "UserName": SAP_USER, 
            "Password": SAP_PASSWORD
        }
        
        try:
            resp = await client.post(f"{SAP_BASE_URL}/Login", json=login_payload)
            
            if resp.status_code != 200:
                print(f"❌ Erro de Login ({resp.status_code}): {resp.text}")
                return

            cookies = resp.cookies
            print("✅ Login OK! Baixando metadados da tabela...")

            # 2. Busca nos Metadados (UserFieldsMD)
            # Filtra apenas os campos que pertencem a essa tabela
            query = f"$filter=TableName eq '{TABLE_NAME}'&$select=Name,Description,Type,SubType,Size"
            
            r = await client.get(f"{SAP_BASE_URL}/UserFieldsMD?{query}", cookies=cookies)
            data = r.json()
            
            fields = data.get('value', [])
            
            if not fields:
                print(f"⚠️ Nenhum campo encontrado. Verifique se o nome da tabela '{TABLE_NAME}' está correto.")
            else:
                print("\n" + "="*100)
                print(f" {'CAMPO JSON (API)':<30} | {'DESCRIÇÃO (Tela do SAP)':<35} | {'TIPO':<10} | {'TAM'}")
                print("="*100)
                
                # Campos padrão do SAP (Sempre existem em tabelas de usuário, mas não vem no UserFieldsMD)
                print(f" {'Code':<30} | {'Código Primário (PK)':<35} | {'String':<10} | 50")
                print(f" {'Name':<30} | {'Descrição do Registro':<35} | {'String':<10} | 100")
                print("-" * 100)

                found_setup = False
                
                for f in fields:
                    # O nome no JSON para UDFs sempre começa com 'U_'
                    json_name = f"U_{f['Name']}"
                    desc = f['Description']
                    tipo = f['Type']
                    size = f.get('Size', 0)
                    
                    # Destaque visual se parecer com setup
                    marker = ""
                    if "setup" in desc.lower() or "prepar" in desc.lower() or "tipo" in desc.lower():
                        marker = "  <-- 🎯 POSSÍVEL SETUP"
                        found_setup = True
                    
                    print(f" {json_name:<30} | {desc:<35} | {tipo:<10} | {size:<4}{marker}")
                
                print("="*100)
                
                if found_setup:
                    print("\n✅ Encontrei campos suspeitos de serem o 'Setup'! Teste enviar 'Y', 'S', '1' ou 'true' para eles.")
                else:
                    print("\n⚠️ Não achei nenhum campo com nome 'Setup' ou 'Preparação'. Procure por campos genéricos como 'U_Tipo' ou 'U_Flag'.")

        except Exception as e:
            print(f"❌ Erro Crítico: {str(e)}")

if __name__ == "__main__":
    asyncio.run(list_all_table_fields())