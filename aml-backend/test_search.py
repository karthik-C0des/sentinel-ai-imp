import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

async def test_search():
    load_dotenv(dotenv_path=r'c:\Users\R KARTHIK\Documents\aml-demo-01\fsi-aml-fraud-detection-main\aml-backend\.env')
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "threatsight360")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db["threatsightEntities"]
    
    # Try different index names
    indices = [
        "entity_resolution_search",
        "entity_search_indexv2",
        "entity_text_search_index",
        "default"
    ]
    
    for index_name in indices:
        print(f"\n--- Testing index: {index_name} ---")
        pipeline = [
            {
                "$search": {
                    "index": index_name,
                    "text": {
                        "query": "James",
                        "path": "name.full"
                    }
                }
            },
            {"$limit": 2}
        ]
        
        try:
            results = await collection.aggregate(pipeline).to_list(length=2)
            print(f"Found {len(results)} results using index {index_name}")
            for r in results:
                name = r.get("name", {}).get("full")
                print(f"  - {name}")
        except Exception as e:
            print(f"Error with index {index_name}: {e}")
            
    client.close()

if __name__ == "__main__":
    asyncio.run(test_search())
