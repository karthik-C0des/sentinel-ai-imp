import asyncio, os, time
from dotenv import load_dotenv
load_dotenv('.env')
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('DB_NAME', 'threatsight360')]
    
    while True:
        cursor = db.threatsightEntities.list_search_indexes()
        indexes = await cursor.to_list(length=None)
        
        ready = 0
        target = ['entity_resolution_text_search', 'entity_vector_search_384_new']
        for idx in indexes:
            if idx['name'] in target:
                print(f"{idx['name']} is {idx.get('status', 'UNKNOWN')}")
                if idx.get('status') == 'READY':
                    ready += 1
        
        if ready == 2:
            print('All indexes are READY!')
            break
            
        print('Waiting 5 seconds...')
        time.sleep(5)

asyncio.run(check())
