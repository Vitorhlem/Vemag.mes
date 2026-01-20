import httpx
import asyncio
import urllib3
import json

# Desabilita avisos de SSL (certificado auto-assinado)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES IGUAIS AO SEU SAP_SYNC.PY ---
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

async def check_fields():
    print(f"🚀 Conectando ao SAP ({SAP_BASE_URL})...")
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # 1. LOGIN
        login_payload = {
            "CompanyDB": SAP_COMPANY_DB, 
            "UserName": SAP_USER, 
            "Password": SAP_PASSWORD
        }
        
        try:
            resp = await client.post(f"{SAP_BASE_URL}/Login", json=login_payload)
            if resp.status_code != 200:
                print(f"❌ Erro no Login: {resp.text}")
                return
            
            print("✅ Login realizado com sucesso!")
            cookies = resp.cookies

            # 2. BUSCAR ESTRUTURA DA TABELA @LGO_CAPONTAMENTO
            # Tenta pegar 1 registro para ver as chaves. Se estiver vazia, pegamos do $metadata (mais complexo), 
            # mas geralmente tem registro.
            print("\n🔍 Consultando tabela @LGO_CAPONTAMENTO...")
            
            # Pegamos apenas 1 registro para ler as chaves
            query_url = f"{SAP_BASE_URL}/LGO_CAPONTAMENTO?$top=1"
            
            resp_table = await client.get(query_url, cookies=cookies)
            
            if resp_table.status_code == 200:
                data = resp_table.json()
                items = data.get('value', [])
                
                if items:
                    print("\n📋 CAMPOS ENCONTRADOS NO SAP:")
                    print("="*40)
                    # Lista todas as chaves (colunas) do primeiro registro
                    first_item = items[0]
                    for key, value in first_item.items():
                        # Filtra apenas os campos de usuário (U_) para facilitar a leitura
                        if key.startswith("U_"):
                            print(f"🔹 {key}  \t(Ex valor: {value})")
                        elif key in ["Code", "Name", "DocEntry"]:
                            print(f"🔸 {key}")
                    print("="*40)
                    print("\n⚠️  Verifique acima se existe 'U_DescricaoItem' e 'U_NomeOperador'.")
                    print("   Se não existirem, você precisará criá-los no SAP ou usar outro campo existente.")
                else:
                    print("⚠️ A tabela @LGO_CAPONTAMENTO existe mas está VAZIA.")
                    print("   Não foi possível ler os campos dinamicamente.")
            else:
                print(f"❌ Erro ao consultar tabela: {resp_table.status_code} - {resp_table.text}")

        except Exception as e:
            print(f"❌ Exceção: {str(e)}")

# Executa o script
if __name__ == "__main__":
    asyncio.run(check_fields())