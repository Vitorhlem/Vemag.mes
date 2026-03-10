import pyodbc
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Importando modelos do TruMachine
from app.crud import crud_user
from app.schemas.user_schema import UserCreate
from app.models.user_model import User, UserRole

# --- CONFIGURAÇÕES DO RM (SQL SERVER) ---
RM_SERVER = "192.168.0.3"
RM_DATABASE = "CORPORERM_teste"
RM_USER = "rm"
RM_PASSWORD = "rm"
# Usando o OPERATOR nativo pois é o que funcionou para você
RM_OPERATOR = "{SQL Server}"

# --- FILTRO FABRIL ---
# Lista de Seções que serão importadas (ignora administrativo)
SECOES_FABRIL = [
    "01.03.06"

]

class RMIntegrationService:
    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.org_id = organization_id

    def get_connection(self):
        conn_str = f'OPERATOR={RM_OPERATOR};SERVER={RM_SERVER};DATABASE={RM_DATABASE};UID={RM_USER};PWD={RM_PASSWORD};TrustServerCertificate=yes;'
        try:
            return pyodbc.connect(conn_str, timeout=10)
        except Exception as e:
            print(f"❌ [RM] Erro Crítico de Conexão SQL: {e}")
            return None

    def eh_fabril(self, cod_secao: str) -> bool:
        """Verifica se a seção do funcionário está na lista de permitidas"""
        if not cod_secao:
            return False
        for prefixo in SECOES_FABRIL:
            if str(cod_secao).startswith(prefixo):
                return True
        return False

    async def sync_employees(self):
        print(f"🔄 [RM] Iniciando sincronização com CARGOS (Filtro Fabril: {SECOES_FABRIL})...")
        
        conn = self.get_connection()
        if not conn:
            print("⚠️ [RM] Abortando: Banco desconectado.")
            return

        employees = []
        try:
            cursor = conn.cursor()
            
            # --- QUERY ATUALIZADA ---
            # Faz JOIN com PFUNCAO (F) para pegar o NOME do Cargo
            sql_query = """
            SELECT 
                P.CHAPA, 
                P.NOME, 
                PP.EMAIL,
                P.CODSITUACAO,
                P.CODSECAO,
                F.NOME AS CARGO
            FROM PFUNC P
            LEFT JOIN PPESSOA PP ON P.CODPESSOA = PP.CODIGO
            LEFT JOIN PFUNCAO F ON P.CODFUNCAO = F.CODIGO AND P.CODCOLIGADA = F.CODCOLIGADA
            WHERE P.CODSITUACAO <> 'D'
            """
            
            cursor.execute(sql_query)
            
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                employees.append(dict(zip(columns, row)))
                
            print(f"📦 [RM] Total de ativos no banco: {len(employees)}. Processando...")
            
        except Exception as e:
            print(f"❌ [RM] Erro na Query: {e}")
            conn.close()
            return
        finally:
            conn.close()

        count_new = 0
        count_updated = 0
        count_skipped_admin = 0

        for emp in employees:
            try:
                chapa = str(emp.get('CHAPA')).strip()
                nome = emp.get('NOME').strip()
                email_rm = emp.get('EMAIL')
                cod_secao = str(emp.get('CODSECAO')).strip()
                cargo_rm = str(emp.get('CARGO') or '').strip() # Pega o cargo ou vazio

                # 1. Filtro Demitido
                if emp.get('CODSITUACAO') == 'D':
                    continue

                # 2. Filtro Fabril
                if not self.eh_fabril(cod_secao):
                    count_skipped_admin += 1
                    continue

                # Lógica de E-mail
                if not email_rm or '@' not in str(email_rm):
                    email_final = f"{chapa}@vemagmes.local"
                else:
                    email_final = str(email_rm).strip().lower()

                # Busca usuário no TruMachine
                existing_user = await crud_user.get_user_by_email(self.db, email=email_final)

                if not existing_user:
                    print(f"👤 [RM] Cadastrando: {nome} | Cargo: {cargo_rm}")
                    
                    user_in = UserCreate(
                        email=email_final,
                        full_name=nome,
                        password="mudar123",
                        role=UserRole.OPERATOR,
                        organization_id=self.org_id,
                        phone=None,
                        job_title=cargo_rm # <--- AQUI SALVAMOS O CARGO AUTOMATICAMENTE
                    )
                    
                    new_user = await crud_user.create(
                        self.db, 
                        user_in=user_in, 
                        organization_id=self.org_id, 
                        role=UserRole.OPERATOR
                    )
                    
                    new_user.employee_id = chapa
                    self.db.add(new_user)
                    count_new += 1
                else:
                    # Atualiza Matrícula e Cargo se mudaram
                    mudou = False
                    if existing_user.employee_id != chapa:
                        existing_user.employee_id = chapa
                        mudou = True
                    
                    if existing_user.job_title != cargo_rm:
                        existing_user.job_title = cargo_rm
                        mudou = True
                        
                    if mudou:
                        self.db.add(existing_user)
                        count_updated += 1
            
            except Exception as e_user:
                print(f"⚠️ Erro chapa {chapa}: {e_user}")
                continue

        await self.db.commit()
        print(f"✅ [RM] Fim: {count_new} novos, {count_updated} atualizados, {count_skipped_admin} ignorados (admin).")