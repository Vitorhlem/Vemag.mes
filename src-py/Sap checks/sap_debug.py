import httpx
import asyncio
import urllib3

# Desabilita avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- SUAS CREDENCIAIS REAIS ---
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

async def debug_sap():
    async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
        print(f"🕵️ Conectando em {SAP_BASE_URL}...")
        
        # 1. Login
        resp = await client.post(f"{SAP_BASE_URL}/Login", json={
            "CompanyDB": SAP_COMPANY_DB, "UserName": SAP_USER, "Password": SAP_PASSWORD
        })
        
        if resp.status_code != 200:
            print(f"❌ Erro de Login: {resp.text}")
            return

        cookies = resp.cookies
        print("✅ Login OK! Buscando informações...")

        # 2. Listar Grupos de Itens (Para descobrir o código certo)
        print("\n📋 LISTA DE GRUPOS DE ITENS (Procure o de Máquinas):")
        print("=" * 60)
        r_groups = await client.get(f"{SAP_BASE_URL}/ItemGroups?$select=Number,GroupName", cookies=cookies)
        for g in r_groups.json().get('value', []):
            print(f"🆔 CÓDIGO: {g['Number']} \t| NOME: {g['GroupName']}")
        print("=" * 60)

        # 3. Espiar os primeiros 10 itens (Para ver como estão cadastrados)
        print("\n📦 AMOSTRA DE 10 ITENS NO BANCO:")
        print("=" * 60)
        # Trazemos ItemCode, Nome, Grupo e se é Valido
        r_items = await client.get(f"{SAP_BASE_URL}/Items?$top=10&$select=ItemCode,ItemName,ItemsGroupCode,Valid", cookies=cookies)
        for i in r_items.json().get('value', []):
            print(f"Item: {i['ItemCode']} | Grupo: {i['ItemsGroupCode']} | Ativo: {i['Valid']} | Desc: {i['ItemName']}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_sap())