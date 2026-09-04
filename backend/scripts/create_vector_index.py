import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

async def run():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['sentinelai']
    coll = db['transactions']
    
    print("Checking search indexes on sentinelai.transactions...")
    try:
        search_idxs = []
        async for idx in coll.list_search_indexes():
            search_idxs.append(idx)
        print("Search indexes:", json.dumps(search_idxs, indent=2))
        
        if not any(idx.get('name') == 'transaction_vector_index' for idx in search_idxs):
            print("Creating transaction_vector_index...")
            await coll.create_search_index({
                "name": "transaction_vector_index",
                "definition": {
                    "mappings": {
                        "dynamic": True,
                        "fields": {
                            "vector_embedding": {
                                "dimensions": 1536,
                                "similarity": "cosine",
                                "type": "knnVector"
                            }
                        }
                    }
                }
            })
            print("Index created! It may take a few minutes to build.")
        else:
            print("Index transaction_vector_index already exists!")
            
            # Check the status
            for idx in search_idxs:
                if idx.get('name') == 'transaction_vector_index':
                    print("Status:", idx.get('status'))
                    
    except Exception as e:
        print("Error with search indexes:", e)

if __name__ == "__main__":
    asyncio.run(run())
