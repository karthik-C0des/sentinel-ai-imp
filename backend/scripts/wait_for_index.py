import asyncio
import os
import time
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

async def run():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['threatsight360']
    coll = db['transactions']
    
    print("Waiting for transaction_vector_index to become READY...")
    
    while True:
        search_idxs = []
        async for idx in coll.list_search_indexes():
            if idx.get("name") == "transaction_vector_index":
                search_idxs.append(idx)
        
        if not search_idxs:
            print("Index not found yet...")
        else:
            status = search_idxs[0].get("status")
            print(f"Status: {status}")
            if status == "READY":
                print("Index is ready!")
                break
            elif status == "FAILED":
                print("Index failed to build.")
                break
                
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run())
