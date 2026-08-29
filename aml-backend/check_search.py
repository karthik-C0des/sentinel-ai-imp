import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_search():
    c = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = c[os.getenv('DB_NAME')]
    coll = db['threatsightEntities']
    
    print("\n--- Testing Atlas Search ---")
    atlas_pipeline = [
        {
            "$search": {
                "index": "entity_resolution_search",
                "text": {
                    "query": "John",
                    "path": "name.full"
                }
            }
        },
        {"$limit": 2},
        {"$project": {"_id": 0, "entityId": 1, "name": 1, "score": {"$meta": "searchScore"}}}
    ]
    try:
        results = await coll.aggregate(atlas_pipeline).to_list(None)
        print(f"Atlas search results count: {len(results)}")
        for r in results:
            print(f"  {r}")
    except Exception as e:
        print("Atlas search error:", e)

    c.close()

if __name__ == '__main__':
    asyncio.run(check_search())
