import httpx
import asyncio
import urllib3
import json

# Desativa avisos de certificado SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIGURAÇÕES DE ACESSO
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

async def fetch_latest_production_routes():
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # 1. AUTENTICAÇÃO
        print("🔐 Conectando ao SAP...")
        login_res = await client.post(f"{SAP_BASE_URL}/Login", json={
            "CompanyDB": SAP_COMPANY_DB, 
            "UserName": SAP_USER, 
            "Password": SAP_PASSWORD
        })
        
        if login_res.status_code != 200:
            print(f"❌ Falha no login: {login_res.text}")
            return
        
        cookies = login_res.cookies

        # 2. BUSCA DOS 3 ÚLTIMOS REGISTROS
        # Usamos $orderby DocEntry desc para pegar os mais novos e $top=3
        print("📡 Coletando os 3 últimos roteiros da Engenharia...")
        params = {
            "$select": "Code,Name,U_Desenho,LGLCROTCollection",
            "$orderby": "DocEntry desc",
            "$top": "3"
        }
        
        # O nome do serviço que confirmamos agora é LGCROT
        res = await client.get(f"{SAP_BASE_URL}/LGCROT", params=params, cookies=cookies)
        
        if res.status_code == 200:
            roteiros = res.json().get('value', [])
            
            print(f"\n✅ Foram encontrados {len(roteiros)} registros recentes.\n")
            print("=" * 60)

            for idx, rot in enumerate(roteiros):
                print(f"📦 [{idx + 1}] PRODUTO: {rot.get('Code')} | {rot.get('Name')}")
                print(f"🖼️  DESENHO: {rot.get('U_Desenho')}")
                print("-" * 60)
                
                # Acessando a aba de operações (LGLCROTCollection)
                etapas = rot.get('LGLCROTCollection', [])
                
                if not etapas:
                    print("   ⚠️  Nenhuma operação cadastrada para este roteiro.")
                else:
                    for etapa in etapas:
                        pos = etapa.get('U_Posicao')
                        cod_op = etapa.get('U_Operacao')
                        descr = etapa.get('U_Descr')
                        maquina = etapa.get('U_CentroTra')
                        
                        # Exibindo os dados formatados
                        print(f"   📍 POS: {pos} | OP: {cod_op} | DESC: {descr.ljust(15)} | C.TRAB: {maquina}")
                
                print("=" * 60)
        else:
            print(f"❌ Erro ao acessar o serviço LGCROT: {res.status_code}")
            print(res.text)

if __name__ == "__main__":
    asyncio.run(fetch_latest_production_routes())