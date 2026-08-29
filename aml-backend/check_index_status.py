import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_index_status():
    load_dotenv(dotenv_path=r'c:\Users\R KARTHIK\Documents\aml-demo-01\fsi-aml-fraud-detection-main\aml-backend\.env')
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "threatsight360")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db["threatsightEntities"]
    
    try:
        cursor = collection.list_search_indexes()
        async for index in cursor:
            if index.get("name") == "entity_resolution_search":
                print(f"Status: {index.get('status')}")
                if index.get('statusDetail'):
                    print(f"Status Detail: {index.get('statusDetail')}")
                return
    except Exception as e:
        print(f"Failed: {e}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(check_index_status())
