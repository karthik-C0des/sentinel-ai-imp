"""
Quick script to check the actual structure of the 'identifiers' field
in MongoDB Atlas and show a few sample documents.
"""
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = (
    "mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY"
    "@aml-demo-cluster.klrgot.mongodb.net/threatsight360"
    "?retryWrites=true&w=majority&appName=aml-demo-cluster"
)
DB_NAME = "threatsight360"
COLLECTION = "threatsightEntities"

async def main():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    col = db[COLLECTION]

    print("=== Sample 3 docs: identifiers field ===")
    async for doc in col.find({}, {"entityId": 1, "identifiers": 1, "_id": 0}).limit(3):
        print(f"\nEntity: {doc.get('entityId')}")
        ids = doc.get("identifiers")
        print(f"  Type of identifiers: {type(ids).__name__}")
        print(f"  Value: {json.dumps(ids, default=str, indent=4)}")

    print("\n=== Check issueDate/expiryDate/verified presence ===")
    # Count docs where identifiers is an array (list)
    arr_count = await col.count_documents({"identifiers": {"$type": "array"}})
    obj_count = await col.count_documents({"identifiers": {"$type": "object"}})
    print(f"  identifiers is array  : {arr_count}")
    print(f"  identifiers is object : {obj_count}")

    # Check if any array element has issueDate
    has_issue_date = await col.count_documents({"identifiers.issueDate": {"$exists": True}})
    has_arr_issue = await col.count_documents({"identifiers": {"$elemMatch": {"issueDate": {"$exists": True}}}})
    print(f"  identifiers.issueDate exists (flat): {has_issue_date}")
    print(f"  identifiers[].issueDate exists (array): {has_arr_issue}")

    client.close()

asyncio.run(main())
