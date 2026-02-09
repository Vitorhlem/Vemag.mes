import httpx
import asyncio
import urllib3

# Desabilita avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIGURAÇÕES DO SAP
SAP_BASE_URL = "https://sap-vemag-sl.skyinone.net:50000/b1s/v1"
SAP_COMPANY_DB = "SBOPRODVEM_0601"
SAP_USER = "manager"
SAP_PASSWORD = "Lago287*"

async def list_all_released_ops_with_routes():
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # 1. LOGIN
        login_payload = {
            "CompanyDB": SAP_COMPANY_DB, 
            "UserName": SAP_USER, 
            "Password": SAP_PASSWORD
        }
        
        login_res = await client.post(f"{SAP_BASE_URL}/Login", json=login_payload)
        if login_res.status_code != 200:
            print(f"❌ Falha no login: {login_res.text}")
            return
        cookies = login_res.cookies

        # 2. BUSCA TODAS AS OPs LIBERADAS
        # Note: Usei 'U_LGO_DocEntryOPsFather' conforme encontrado no seu sap_sync.py
        fields = "DocumentNumber,U_LGO_DocEntryOPsFather,ItemNo,ProductDescription,ProductionOrderStatus"
        query = f"$select={fields}&$filter=ProductionOrderStatus eq 'boposReleased'&$orderby=DocumentNumber desc"
        
        print(f"\n🚀 [SAP] Buscando todas as Ordens de Produção Liberadas...")
        
        try:
            response = await client.get(f"{SAP_BASE_URL}/ProductionOrders?{query}", cookies=cookies)
            
            if response.status_code != 200:
                print(f"❌ Erro ao buscar OPs: {response.status_code}")
                print(f"Dica: Se o erro for 400, verifique se o campo 'U_LGO_DocEntryOPsFather' está correto no seu SAP.")
                return

            ops = response.json().get('value', [])
            
            if not ops:
                print("⚠️ Nenhuma OP liberada encontrada.")
                return

            print(f"✅ Encontradas {len(ops)} O.Ps. Verificando roteiros na LGCROT...\n")
            print(f"{'OP (Pai)':<18} | {'DocNum':<8} | {'Item':<15} | {'Roteiro?'}")
            print("-" * 70)

            for op in ops:
                # Captura os dados da OP
                op_father = op.get('U_LGO_DocEntryOPsFather') or "Sem Pai"
                doc_num = op.get('DocumentNumber')
                item_code = op.get('ItemNo')

                # 3. BUSCA O ROTEIRO NA LGCROT PELO ITEM
                query_rot = f"$select=Code&$filter=Code eq '{item_code}'"
                res_rot = await client.get(f"{SAP_BASE_URL}/LGCROT?{query_rot}", cookies=cookies)
                
                route_status = "❌ NÃO"
                if res_rot.status_code == 200:
                    rot_data = res_rot.json().get('value', [])
                    if rot_data:
                        route_status = "✅ SIM"
                
                print(f"{str(op_father):<18} | {str(doc_num):<8} | {str(item_code):<15} | {route_status}")

            print("-" * 70)
            print(f"🏁 Concluído: {len(ops)} O.Ps processadas.")

        except Exception as e:
            print(f"💥 Erro crítico: {str(e)}")

        finally:
            await client.post(f"{SAP_BASE_URL}/Logout", cookies=cookies)

if __name__ == "__main__":
    asyncio.run(list_all_released_ops_with_routes())