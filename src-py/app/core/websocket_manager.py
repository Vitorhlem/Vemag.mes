from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: int):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = []
        self.active_connections[org_id].append(websocket)

    def disconnect(self, websocket: WebSocket, org_id: int):
        if org_id in self.active_connections:
            if websocket in self.active_connections[org_id]:
                self.active_connections[org_id].remove(websocket)

    async def broadcast(self, message: dict, org_id: int):
        """Envia mensagem apenas para os sockets da organização específica"""
        if org_id in self.active_connections:
            for connection in list(self.active_connections[org_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Erro ao enviar WS: {e}")

manager = ConnectionManager()