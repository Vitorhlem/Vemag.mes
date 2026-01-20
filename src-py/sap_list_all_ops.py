print("🚀 LISTANDO TODOS OS CAMPOS (CHAVES) DA OP...", flush=True)

import httpx
import asyncio
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

async def dump_keys():
    async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
        # Login
        await client.post(f"{SAP_BASE_URL}/Login", json={
            "CompanyDB": SAP_COMPANY_DB, "UserName": SAP_USER, "Password": SAP_PASSWORD
        })
        
        # Pega 1 OP liberada SEM FILTRO DE CAMPOS ($select) para vir tudo
        # Note que removi o $select para o SAP mandar o objeto completo
        query = "$top=1&$filter=ProductionOrderStatus eq 'boposReleased'"
        
        r = await client.get(f"{SAP_BASE_URL}/ProductionOrders?{query}", cookies=client.cookies)
        
        if r.status_code == 200:
            data = r.json()
            items = data.get('value', [])
            if items:
                op = items[0]
                print("\n🔑 NOMES DOS CAMPOS ENCONTRADOS (Copie isso):")
                print("=" * 80)
                # Ordena para facilitar a leitura
                keys = sorted(op.keys())
                for k in keys:
                    # Imprime apenas se não for U_ (já conhecemos os U_)
                    if not k.startswith("U_"):
                        print(f"{k}")
                print("=" * 80)
            else:
                print("Nenhuma OP encontrada.")
        else:
            print(f"Erro: {r.text}")

if __name__ == "__main__":
    asyncio.run(dump_keys())