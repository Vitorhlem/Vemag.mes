# src-py/Dockerfile CORRIGIDO v3

FROM python:3.10-slim

WORKDIR /app

# 1. Instala dependências do sistema e ferramentas de chave
# - gnupg e curl são pré-requisitos
# - unixodbc-dev é necessário para compilar bibliotecas python que usam ODBC
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    gnupg \
    ca-certificates \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Configura o repositório do SQL Server (Correção da Chave GPG)
# - Baixa a chave e salva EXATAMENTE onde o arquivo .list espera (/usr/share/keyrings/microsoft-prod.gpg)
# - Adiciona o repositório do Debian 12 (Bookworm)
# - Instala o driver ODBC 17
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# 3. Instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia o código fonte
COPY . .

# 5. Comando de inicialização
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]