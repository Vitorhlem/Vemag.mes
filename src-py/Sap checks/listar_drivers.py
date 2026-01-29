import pyodbc

print("📋 Drivers ODBC instalados nesta máquina:")
drivers = pyodbc.drivers()
for d in drivers:
    print(f"   👉 {d}")

print("\nCopie exatamente um dos nomes acima (preferência para 'ODBC Driver X for SQL Server')")