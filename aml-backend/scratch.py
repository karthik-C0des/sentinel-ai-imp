import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check():
    c = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = c[os.getenv('DB_NAME')]
    
    try:
        idxs = []
        async for idx in db.threatsightEntities.list_search_indexes():
            idxs.append(idx)
        print(json.dumps(idxs, indent=2))
    except Exception as e:
        print("Error:", e)
    
    c.close()

if __name__ == '__main__':
    asyncio.run(check())
