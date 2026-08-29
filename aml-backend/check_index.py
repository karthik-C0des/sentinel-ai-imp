import asyncio, os
from dotenv import load_dotenv
load_dotenv('.env')
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('DB_NAME', 'threatsight360')]
    
    cursor = db.threatsightEntities.list_search_indexes()
    indexes = await cursor.to_list(length=None)
    for idx in indexes:
        if idx['name'] == 'entity_resolution_search':
            print(f"entity_resolution_search is: {idx}")
        else:
            print(f"Found: {idx['name']}")

asyncio.run(check())
