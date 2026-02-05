# Crie este arquivo: src-py/app/core/websocket_manager.py
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Envia a mensagem para todo mundo que estiver com o Andon aberto
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Remove conexões mortas
                self.active_connections.remove(connection)

manager = ConnectionManager()