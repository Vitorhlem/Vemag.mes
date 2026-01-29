print("🚀 INICIANDO INSPEÇÃO DE CAMPOS SAP...", flush=True)

import httpx
import asyncio
import urllib3
import json

# Desabilita avisos de segurança (HTTPS não verificado)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES ---
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

async def inspect_fields():
    async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
        print(f"🔐 Autenticando em {SAP_BASE_URL}...", flush=True)
        
        # 1. Login
        try:
            resp = await client.post(f"{SAP_BASE_URL}/Login", json={
                "CompanyDB": SAP_COMPANY_DB, "UserName": SAP_USER, "Password": SAP_PASSWORD
            })
            
            if resp.status_code != 200:
                print(f"❌ Erro de Login: {resp.text}")
                return

            cookies = resp.cookies
            print("✅ Login OK. Buscando OPs Liberadas...", flush=True)

            # --- CORREÇÃO AQUI: boposReleased em vez de bost_Released ---
            query = "$top=1&$filter=ProductionOrderStatus eq 'boposReleased'"
            
            r = await client.get(f"{SAP_BASE_URL}/ProductionOrders?{query}", cookies=cookies)
            
            if r.status_code == 200:
                data = r.json()
                items = data.get('value', [])
                
                if not items:
                    print("⚠️ Nenhuma OP encontrada com status 'boposReleased'.")
                    return

                op = items[0]
                
                print("\n📋 LISTA DE CAMPOS ENCONTRADOS NA OP:")
                print("=" * 60)
                
                custom_fields = []
                standard_fields = []
                
                for key, value in op.items():
                    if key.startswith("U_"):
                        custom_fields.append(key)
                    else:
                        standard_fields.append(key)
                
                print(f"🔹 CAMPOS DE USUÁRIO (Customizados):")
                if custom_fields:
                    for f in sorted(custom_fields):
                        print(f"   👉 {f}  (Valor atual: {str(op[f])[:50]})")
                else:
                    print("   (Nenhum campo customizado encontrado)")
                    
                print("-" * 60)
                print(f"🔹 CAMPOS PADRÃO (Principais):")
                keys_to_show = ["DocNum", "ItemCode", "ProdName", "PlannedQty", "ProductionOrderStatus"]
                for k in keys_to_show:
                    if k in op:
                        print(f"   • {k}: {op[k]}")

                print("=" * 60)
                
            else:
                print(f"❌ Erro ao buscar OPs: {r.status_code}")
                print(f"   Detalhe: {r.text}")

        except Exception as e:
            print(f"❌ Erro Crítico: {str(e)}")

if __name__ == "__main__":
    asyncio.run(inspect_fields())