import httpx
import asyncio

# --- SEUS DADOS DE ACESSO ---
# Preencha com os dados reais do seu SAP
SAP_URL = "https://sap-vemag-sl.skyinone.net:443/b1s/v1"
DB = "SBOPRODVEM_0601"
USER = "manager"
PASSWORD = "Lago287*"

async def diagnose():
    print(f"🕵️ Conectando ao SAP em {SAP_URL}...")
    
    async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
        # 1. Login
        resp = await client.post(f"{SAP_URL}/Login", json={
            "CompanyDB": DB, "UserName": USER, "Password": PASSWORD
        })
        
        if resp.status_code != 200:
            print(f"❌ Erro no Login: {resp.text}")
            return
            
        print("✅ Login OK! Buscando Grupos de Itens...")
        cookies = resp.cookies

        # 2. Busca Grupos de Itens (ItemGroups)
        # Traz o Código (Number) e o Nome (GroupName)
        r_groups = await client.get(f"{SAP_URL}/ItemGroups?$select=Number,GroupName", cookies=cookies)
        
        if r_groups.status_code == 200:
            groups = r_groups.json().get('value', [])
            print("\n📋 LISTA DE GRUPOS DE ITENS NO SEU SAP:")
            print("="*40)
            for g in groups:
                print(f"🆔 CÓDIGO: {g['Number']}  |  NOME: {g['GroupName']}")
            print("="*40)
            print("👉 Procure acima qual é o grupo das suas MÁQUINAS e me diga o CÓDIGO.")
        else:
            print(f"❌ Erro ao buscar grupos: {r_groups.text}")

        # 3. (Opcional) Espiar um Item de exemplo para ver os campos
        # Se você souber o código de uma máquina (ex: 'MQ-001'), coloque abaixo
        EXEMPLO_MAQUINA = "INSIRA_CODIGO_AQUI_SE_QUISER_TESTAR"
        
        if EXEMPLO_MAQUINA != "INSIRA_CODIGO_AQUI_SE_QUISER_TESTAR":
            print(f"\n🔍 Espiando dados da máquina: {EXEMPLO_MAQUINA}...")
            r_item = await client.get(f"{SAP_URL}/Items('{EXEMPLO_MAQUINA}')", cookies=cookies)
            if r_item.status_code == 200:
                print(r_item.json()) # Vai imprimir TUDO que tem na máquina
            else:
                print("Item não encontrado.")

if __name__ == "__main__":
    asyncio.run(diagnose())