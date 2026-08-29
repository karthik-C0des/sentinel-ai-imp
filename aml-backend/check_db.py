import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    db = AsyncIOMotorClient('mongodb://localhost:27017')['threatsight360']
    doc = await db.threatsightEntities.find_one({'entityId': 'ENT-0001'}, {'_id': 0})
    print(json.dumps(doc.get('identifiers'), default=str, indent=2))
    
    # Try with curl to API directly as well if API is up
    import urllib.request
    try:
        req = urllib.request.urlopen("http://localhost:8000/api/entities/ENT-0001")
        print("\n--- API RESPONSE ---")
        api_data = json.loads(req.read().decode('utf-8'))
        print(json.dumps(api_data.get('data', {}).get('identifiers'), indent=2))
    except Exception as e:
        print("API Error:", e)

asyncio.run(main())
