import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.operations import SearchIndexModel

load_dotenv('.env')

async def setup():
    print("Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('DB_NAME', 'threatsight360')]
    collection = db.threatsightEntities
    
    print("\n1. Creating entity_resolution_search (Text Index)")
    try:
        text_index = SearchIndexModel(
            definition={"mappings": {"dynamic": True}},
            name="entity_resolution_search",
            type="search"
        )
        await collection.create_search_index(text_index)
        print("Successfully initiated entity_resolution_search index creation")
    except Exception as e:
        print(f"Text index creation returned: {e}")

    print("\n2. Creating entity_vector_search_384 (Vector Index)")
    try:
        vector_index = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "numDimensions": 384,
                        "path": "profileEmbedding",
                        "similarity": "cosine",
                        "type": "vector"
                    },
                    {
                        "path": "entityType",
                        "type": "filter"
                    }
                ]
            },
            name="entity_vector_search_384",
            type="vectorSearch"
        )
        await collection.create_search_index(vector_index)
        print("Successfully initiated entity_vector_search_384 index creation")
    except Exception as e:
        print(f"Vector index creation returned: {e}")
        
    print("\nPlease wait a few minutes for the indexes to finish building in Atlas.")

asyncio.run(setup())
