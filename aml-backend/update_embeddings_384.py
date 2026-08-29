import asyncio
import os
import sys
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Ensure the backend directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reference.mongodb_core_lib import MongoDBRepository
from repositories.impl.vector_search_repository import VectorSearchRepository

async def main():
    load_dotenv(dotenv_path=".env")
    uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('DB_NAME', 'threatsight360')
    
    print(f"Connecting to MongoDB database: {db_name}...")
    mongo_repo = MongoDBRepository(uri, db_name)
    vector_repo = VectorSearchRepository(mongo_repo)
    
    # Use motor directly for iteration
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db['threatsightEntities']
    
    total_docs = await collection.count_documents({})
    print(f"Found {total_docs} entities. Starting re-embedding process...")
    
    processed = 0
    updated = 0
    errors = 0
    
    # Process in chunks to avoid overloading memory
    cursor = collection.find({})
    async for doc in cursor:
        processed += 1
        entity_id = doc.get('entityId') or str(doc.get('_id'))
        
        try:
            # Generate the new 384-dimensional embedding
            embedding = await vector_repo.generate_entity_embedding(doc)
            
            if embedding and len(embedding) == 384:
                # Update the document with the new embedding
                await collection.update_one(
                    {'_id': doc['_id']},
                    {
                        '$set': {
                            'profileEmbedding': embedding,
                            'identifierEmbedding': embedding, # Usually they share this structure for mock data
                            'behavioralEmbedding': embedding
                        }
                    }
                )
                updated += 1
            else:
                print(f"Warning: Generated embedding for {entity_id} was invalid or wrong size.")
                errors += 1
                
        except Exception as e:
            print(f"Error processing entity {entity_id}: {e}")
            errors += 1
            
        if processed % 10 == 0:
            print(f"Progress: {processed}/{total_docs} entities processed. ({updated} updated, {errors} errors)")
            
    print(f"\nDone! Successfully updated {updated} entities to 384 dimensions.")

if __name__ == '__main__':
    asyncio.run(main())
