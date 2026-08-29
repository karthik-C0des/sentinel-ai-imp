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
    
    results = await collection.find({}).to_list(length=10)
    print("Sample entities:")
    for r in results:
        name = r.get('name', {})
        if isinstance(name, dict):
            print(f" - {name.get('full')} (ID: {r.get('entityId', r.get('_id'))})")
        else:
            print(f" - {name} (ID: {r.get('entityId', r.get('_id'))})")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(check_data())
