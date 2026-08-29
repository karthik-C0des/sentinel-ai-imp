import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_data():
    load_dotenv(dotenv_path=r'c:\Users\R KARTHIK\Documents\aml-demo-01\fsi-aml-fraud-detection-main\aml-backend\.env')
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "threatsight360")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db["threatsightEntities"]
    
    count = await collection.count_documents({})
    print(f"Total documents in threatsightEntities: {count}")
    
    results = await collection.find({"name.full": {"$regex": "Lisa", "$options": "i"}}).to_list(length=5)
    print(f"Documents matching 'Lisa': {len(results)}")
    
    for r in results:
        print(f" - {r.get('name', {}).get('full')}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(check_data())
