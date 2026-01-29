import socket
import sys

host = "sap-vemag-sl.skyinone.net"
port = 50000

print(f"🕵️  Testando conexão com {host}:{port}...")

try:
    # Tenta conectar via TCP (como um Telnet)
    sock = socket.create_connection((host, port), timeout=5)
    print("✅  SUCESSO! A porta está aberta e acessível.")
    sock.close()
except socket.timeout:
    print("❌  TIMEOUT: O servidor não respondeu. Provavelmente Firewall ou IP errado.")
except ConnectionRefusedError:
    print("❌  RECUSADO: O servidor existe, mas a porta 50000 está fechada.")
except socket.gaierror:
    print("❌  DNS: Não consegui encontrar esse endereço (sap-vemag-sl...).")
except Exception as e:
    print(f"❌  ERRO: {e}")