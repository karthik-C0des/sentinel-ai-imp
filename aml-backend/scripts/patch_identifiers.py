"""
Patch script: adds issueDate, expiryDate, and verified to every identifier
object inside the identifiers array for all entities in MongoDB Atlas.
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = (
    "mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY"
    "@aml-demo-cluster.klrgot.mongodb.net/sentinelai"
    "?retryWrites=true&w=majority&appName=aml-demo-cluster"
)
DB_NAME = "sentinelai"
COLLECTION = "sentinelaiEntities"

random.seed(42)

def rand_past_date(max_years_ago: int = 15) -> str:
    """Return a random ISO date in the past."""
    days_ago = random.randint(365, max_years_ago * 365)
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%d")

def rand_future_date(min_days: int = 30, max_days: int = 3650) -> str:
    """Return a random ISO date in the future."""
    days_ahead = random.randint(min_days, max_days)
    dt = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    return dt.strftime("%Y-%m-%d")

async def main():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    col = db[COLLECTION]

    # Only patch docs where identifiers is an array AND
    # the first element is missing issueDate
    query = {
        "identifiers": {"$type": "array", "$elemMatch": {"issueDate": {"$exists": False}}}
    }

    total = await col.count_documents(query)
    print(f"Found {total} entities to patch...")

    patched = 0
    async for doc in col.find(query, {"_id": 1, "identifiers": 1}):
        identifiers = doc.get("identifiers", [])
        if not isinstance(identifiers, list):
            continue

        updated_ids = []
        for id_obj in identifiers:
            if not isinstance(id_obj, dict):
                updated_ids.append(id_obj)
                continue
            # Add missing fields with realistic random values
            patched_id = dict(id_obj)
            if "issueDate" not in patched_id:
                patched_id["issueDate"] = rand_past_date(15)
            if "expiryDate" not in patched_id:
                patched_id["expiryDate"] = rand_future_date(30, 3650)
            if "verified" not in patched_id:
                patched_id["verified"] = random.random() > 0.2  # 80% verified
            updated_ids.append(patched_id)

        await col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"identifiers": updated_ids}}
        )
        patched += 1
        if patched % 50 == 0:
            print(f"  Patched {patched}/{total}...")

    print(f"\nDone! Patched {patched} entities.")

    # Verify
    remaining = await col.count_documents(
        {"identifiers": {"$elemMatch": {"issueDate": {"$exists": False}}}}
    )
    print(f"Entities still missing issueDate: {remaining}")

    # Show a sample
    import json
    sample = await col.find_one(
        {"identifiers": {"$elemMatch": {"issueDate": {"$exists": True}}}},
        {"entityId": 1, "identifiers": 1, "_id": 0}
    )
    if sample:
        print(f"\nSample after patch:")
        print(json.dumps(sample, default=str, indent=2))

    client.close()

asyncio.run(main())
