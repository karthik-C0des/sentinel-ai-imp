import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['leafy_bank_bian']
    coll = db['transactions']
    
    print("Checking indexes...")
    idxs = await coll.index_information()
    print("Regular indexes:", idxs)
    
    try:
        search_idxs = []
        async for idx in coll.list_search_indexes():
            search_idxs.append(idx)
        print("Search indexes:", search_idxs)
    except Exception as e:
        print("Error getting search indexes:", e)

if __name__ == "__main__":
    asyncio.run(run())
