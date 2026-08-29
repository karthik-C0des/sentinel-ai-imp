import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def fix_index():
    load_dotenv(dotenv_path=r'c:\Users\R KARTHIK\Documents\aml-demo-01\fsi-aml-fraud-detection-main\aml-backend\.env')
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "threatsight360")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db["threatsightEntities"]
    
    # We will get the current definition, fix it, and update it.
    try:
        cursor = collection.list_search_indexes()
        index_def = None
        async for index in cursor:
            if index.get("name") == "entity_resolution_search":
                # Some drivers return the definition in 'latestDefinition' if it failed
                if "latestDefinition" in index:
                    index_def = index["latestDefinition"]
                elif "definition" in index:
                    index_def = index["definition"]
                
                break
                
        if not index_def:
            print("Index not found.")
            return

        print("Original definition mapping for score:", 
              index_def['mappings']['fields']['riskAssessment']['fields']['overall']['fields']['score'])
              
        # Remove 'boundaries' from the score mapping
        if 'boundaries' in index_def['mappings']['fields']['riskAssessment']['fields']['overall']['fields']['score']:
            del index_def['mappings']['fields']['riskAssessment']['fields']['overall']['fields']['score']['boundaries']
            
        print("Updated definition mapping for score:", 
              index_def['mappings']['fields']['riskAssessment']['fields']['overall']['fields']['score'])

        print("Updating index...")
        await collection.update_search_index("entity_resolution_search", index_def)
        print("Update command sent. It may take a few minutes to build.")
        
    except Exception as e:
        print(f"Failed: {e}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_index())
