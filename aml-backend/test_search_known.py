import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def test_search():
    load_dotenv(dotenv_path=r'c:\Users\R KARTHIK\Documents\aml-demo-01\fsi-aml-fraud-detection-main\aml-backend\.env')
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "threatsight360")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db["threatsightEntities"]
    
    pipeline = [
        {
            "$search": {
                "index": "entity_resolution_search",
                "text": {
                    "query": "Ahmed",
                    "path": "name.full"
                }
            }
        },
        {"$limit": 2}
    ]
    
    try:
        results = await collection.aggregate(pipeline).to_list(length=2)
        print(f"Found {len(results)} results using index entity_resolution_search for 'Ahmed'")
        for r in results:
            name = r.get("name", {}).get("full")
            print(f"  - {name}")
    except Exception as e:
        print(f"Error: {e}")
            
    client.close()

if __name__ == "__main__":
    asyncio.run(test_search())
