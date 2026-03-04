import asyncio
from app.db.session import SessionLocal
from app import crud
from sqlalchemy import select
from app.models.machine_model import Machine

async def get_valid_truck_id():
    async with SessionLocal() as db:
        # Busca o primeiro veículo do banco
        result = await db.execute(select(Machine))
        machine = result.scalars().first()
        
        if machine:
            print("\n" + "="*50)
            print(f"🚛 VEÍCULO ENCONTRADO!")
            print(f"MODELO: {machine.model}")
            print(f"PLACA: {machine.license_plate}")
            print(f"✅ COPIE ESTE ID PARA O SCRIPT: {machine.id}")
            print("="*50 + "\n")
        else:
            print("\n❌ Nenhum veículo encontrado no banco. Crie um primeiro!")

if __name__ == "__main__":
    asyncio.run(get_valid_truck_id())