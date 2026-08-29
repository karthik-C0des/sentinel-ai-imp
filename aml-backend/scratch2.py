import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check():
    c = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = c[os.getenv('DB_NAME')]
    coll = db['threatsightEntities']
    
    try:
        async for idx in coll.list_search_indexes():
            print(f"Name: {idx.get('name')}, Status: {idx.get('status')}")
    except Exception as e:
        print("Error:", e)
    
    c.close()

if __name__ == '__main__':
    asyncio.run(check())
