import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SapMachineStrictFetcher:
    def __init__(self, base_url, company_db, username, password):
        self.base_url = base_url
        self.cookies = None
        self.credentials = {
            "CompanyDB": company_db,
            "UserName": username,
            "Password": password
        }

        # ====================================================================
        # 1. LISTA NEGRA (CRITÉRIO DE ELIMINAÇÃO IMEDIATA)
        # Se tiver QUALQUER uma dessas palavras, o item é descartado.
        # ====================================================================
        self.KILL_LIST = [
            # --- Serviços ---
            "SERVIÇO", "SERVICO", "MANUTENÇÃO", "REFORMA", "FRETE", "LOCACAO",
            "OPER.", "INSUMO", "TRANSPORTE",
            
            # --- Movimentação e Elevação (Você pediu para remover) ---
            "PONTE ROLANTE", "PORTICO", "PÓRTICO", "TALHA", "GUINCHO", 
            "GANCHO", "ESTROPO", "CINTA", "MOVIMENTACAO",
            
            # --- Ferramentas Manuais / Portáteis / Pequenas ---
            "RETIFICADEIRA", # Geralmente é a manual (MG 1500, etc). A industrial chamamos de RETIFICA
            "DREMEL", "LIXADEIRA", "ESMERILHADEIRA", "PARAFUSADEIRA",
            "FURADEIRA DE IMPACTO", "FURADEIRA MANUAL", 
            "TORNO DE BANCADA", "PRATIKO", # Torno pequeno
            "SOPRADOR", "PISTOLA", "MARTELETE", 
            "MANUAL", "PORTATIL", "PNEUMATICA", "PNEUMÁTICA",
            
            # --- Marcas de Ferramentas Manuais (Geralmente Lixo para o MES) ---
            "MEGA", "PUMA", "DEWALT", "BOSCH", "MAKITA", "SKIL", "VONDER",
            
            # --- Peças, Partes e Acessórios (O maior volume de lixo) ---
            "MESA", "PLACA", "CASTANHA", "LUNETA", "BASE", "COLUNA", 
            "CABECOTE", "CABEÇOTE", "FUSO", "EIXO", "ROLAMENTO", "MANCAL",
            "PROTECAO", "PROTEÇÃO", "CAIXA", "TAMPA", "ESTRUTURA", "CARCACA",
            "ANEL", "PINCA", "PINÇA", "BUCHA", "PORCA", "PARAFUSO", "ARRUELA",
            "FLANGE", "ENGRENAGEM", "LUVA", "COTOVELO", "BOCAL", "CONEXAO",
            "MANGUEIRA", "CABO", "TERMINAL", "VALVULA", "RELE", "SENSOR",
            "VENTILADOR", "VENTOINHA", "MOTOR", "BOMBA", "PAINEL", "TECLADO",
            "MANIVELA", "MONITOR", "CNC MODELO", "CNC COMPLETO", # Peça do comando, não a máquina
            "MANDRIL", # Mandril isolado é peça. Mandrilhadora é máquina (tratado na lógica)
            "BICO", "TOCHA", "ELEMENTO FILTRANTE", "FILTRO",
            "PRATO", "CESTO", "TAMBOR", "ROLO", "ROLETE",
            
            # --- Consumíveis e Materiais ---
            "SERRA DE FITA" # Se for a lâmina (tem medidas ou marca Starrett)
        ]
        
        # Termos específicos que identificam LÂMINAS de serra (não a máquina)
        self.BLADE_INDICATORS = ["STARRET", "STARRETT", "M42", "X 0,", "X 4", "COMPRIMENTO"]

        # ====================================================================
        # 2. LISTA BRANCA (CRITÉRIO DE ACEITE)
        # O item DEVE conter um destes termos para ser considerado.
        # ====================================================================
        self.VALID_MACHINES = [
            "TORNO", 
            "MANDRILHADORA", "MANDRILADORA",
            "FRESADORA",
            "CENTRO DE USINAGEM", "CENTRO USINAGEM",
            "FURADEIRA RADIAL", "FURADEIRA DE COLUNA",
            "RETIFICA PLANA", "RETIFICA CILINDRICA", # Sê especifico para evitar retificadeira de mão
            "RETIFICA DE BARRAMENTO",
            "PRENSA HIDRAULICA", "PRENSA EXCENTRICA", # Sê especifico para evitar 'prensa cabo'
            "GUILHOTINA", "DOBRADEIRA", 
            "CALANDRA", # Cuidado com 'Calandrada'
            "INJETORA",
            "CORTE PLASMA", "CORTE A LASER", 
            "SERRA DE FITA" # Só passa se não tiver indicador de lâmina
        ]

    def login(self):
        try:
            res = requests.post(f"{self.base_url}/Login", json=self.credentials, verify=False)
            if res.status_code == 200:
                self.cookies = res.cookies
                return True
            return False
        except: return False

    def is_valid(self, name):
        if not name: return False
        up = name.upper()

        # 1. ANALISE DE SERRA DE FITA (Caso Especial)
        if "SERRA" in up and "FITA" in up:
            # Se tiver marca de lâmina ou medida pequena, é lixo
            for ind in self.BLADE_INDICATORS:
                if ind in up: return False
            # Se tiver "MANUAL", é lixo
            if "MANUAL" in up: return False
            # Se passou, é máquina
            return True

        # 2. FILTRO "KILL LIST" (Se tiver palavra proibida, morre)
        for bad in self.KILL_LIST:
            # Truque para não matar "MANDRILHADORA" por causa de "MANDRIL"
            if bad == "MANDRIL" and ("MANDRILHADORA" in up or "MANDRILADORA" in up):
                continue
            
            # Truque para não matar "MESA DE CORTE" por causa de "MESA"
            if bad == "MESA" and "MESA DE CORTE" in up:
                continue

            if bad in up:
                return False

        # 3. FILTRO EXTRA: PALAVRAS QUE INDICAM PROCESSO/MATERIAL
        # Ex: "CHAPA CALANDRADA" -> Contém CALANDRA, mas é lixo.
        if "CALANDRADA" in up or "CALANDRADO" in up: return False
        if "USINADA" in up or "USINADO" in up: return False # Ex: "Peça Usinada"
        if "PRENSA CABO" in up: return False

        # 4. FILTRO DE INCLUSÃO (Tem que ser máquina)
        for mach in self.VALID_MACHINES:
            if mach in up:
                return True

        return False

    def run(self):
        if not self.cookies and not self.login(): 
            print("Falha login"); return

        print("--- INICIANDO FILTRAGEM RIGOROSA ---")
        # Puxa apenas Ativos Fixos para ajudar no filtro inicial
        next_link = f"{self.base_url}/Items?$select=ItemCode,ItemName&$filter=Frozen eq 'N' and ItemType eq 'itFixedAssets'"
        
        count = 0
        while next_link:
            try:
                headers = {"Prefer": "odata.maxpagesize=1000"}
                res = requests.get(next_link, cookies=self.cookies, verify=False, headers=headers)
                data = res.json()
                
                for item in data.get('value', []):
                    name = item.get('ItemName')
                    code = item.get('ItemCode')
                    
                    if self.is_valid(name):
                        print(f"[{code}] {name}")
                        count += 1

                if "odata.nextLink" in data:
                    skip = data["odata.nextLink"]
                    next_link = f"{self.base_url}/{skip}" if skip.startswith("Items") else f"{self.base_url}/{skip}"
                else: next_link = None
            except Exception as e: 
                print(e); break
        
        print(f"\nTotal Máquinas Encontradas: {count}")

if __name__ == "__main__":
    SAP_CONFIG = {
        "base_url": "https://sap-vemag-sl.skyinone.net:50000/b1s/v1",
        "company_db": "SBOPRODVEM_0601",
        "username": "manager",
        "password": "Lago287*"
    }
    fetcher = SapMachineStrictFetcher(**SAP_CONFIG)
    fetcher.run()