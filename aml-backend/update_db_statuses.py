import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random
from dotenv import load_dotenv

load_dotenv()

async def update_statuses():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "threatsight360")
    print(f"Connecting to MongoDB: {mongo_uri.split('@')[-1]} (DB: {db_name})")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    collection = db["threatsightEntities"]
    
    # Fetch all entities
    cursor = collection.find({})
    entities = await cursor.to_list(length=None)
    print(f"Found {len(entities)} entities to check.")
    
    updated_count = 0
    for entity in entities:
        # Check risk score and watchlist status to assign a realistic status
        risk_assessment = entity.get("riskAssessment", {})
        overall = risk_assessment.get("overall", {})
        risk_score = overall.get("score", 50)
        risk_level = overall.get("level", "medium")
        
        # Check watchlisted status
        watchlist_flags = entity.get("watchlistFlags", {})
        watchlisted = watchlist_flags.get("isOnWatchlist", False)
        
        if watchlisted or risk_level in ["high", "critical"]:
            status = "under_review"
        elif risk_score < 20:
            status = "inactive"
        else:
            status = "active"
            
        # Update document in DB if it has no status or different status
        result = await collection.update_one(
            {"_id": entity["_id"]},
            {"$set": {"status": status}}
        )
        if result.modified_count > 0 or not entity.get("status"):
            updated_count += 1
            
    print(f"Successfully updated/set status for {updated_count} entities.")
    client.close()

if __name__ == "__main__":
    asyncio.run(update_statuses())
