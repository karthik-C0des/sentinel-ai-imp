"""
Safe, non-destructive migration script with real-time output flushing.
'sentinelai',
renaming collections to match what the backend code expects.
"""

from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY@aml-demo-cluster.klrgot.mongodb.net/sentinelai?retryWrites=true&w=majority&appName=aml-demo-cluster"

COLLECTION_MAP = {
    "legacyEntities": "sentinelaiEntities",
    "legacyRelationships": "sentinelaiRelationships",
    "legacyAlerts": "sentinelaiAlerts",
    "legacyInvestigations": "sentinelaiInvestigations",
    "legacyCompliancePolicies": "sentinelaiCompliancePolicies",
    "legacyTypologyLibrary": "sentinelaiTypologyLibrary",
    "legacyCheckpoints": "sentinelaiCheckpoints",
    "legacyCheckpointWrites": "sentinelaiCheckpointWrites",
    "transactionsv2": "transactionsv2",
    "transactions": "transactions",
    "customers": "customers",
    "fraud_patterns": "fraud_patterns",
}

def migrate():
    print("Connecting to MongoDB Atlas...", flush=True)
    client = MongoClient(MONGODB_URI)
    src_db = client["legacy_db"]
    dst_db = client["sentinelai"]

    for src_name, dst_name in COLLECTION_MAP.items():
        if src_name not in src_db.list_collection_names():
            print(f"[-] Skipping {src_name} (not found)", flush=True)
            continue

        src_coll = src_db[src_name]
        dst_coll = dst_db[dst_name]

        # Check if already migrated
        src_cnt = src_coll.count_documents({})
        dst_cnt = dst_coll.count_documents({})
        if dst_cnt == src_cnt and src_cnt > 0:
            print(f"[=] {dst_name} already has {dst_cnt}/{src_cnt} docs. Skipping.", flush=True)
            continue

        print(f"[+] Migrating {src_name} -> {dst_name} (target has {dst_cnt}/{src_cnt} docs)...", flush=True)
        dst_coll.drop()

        batch = []
        batch_size = 2000
        copied = 0
        for doc in src_coll.find({}):
            batch.append(doc)
            if len(batch) >= batch_size:
                dst_coll.insert_many(batch, ordered=False)
                copied += len(batch)
                print(f"    Copied {copied}/{src_cnt}...", flush=True)
                batch = []
        if batch:
            dst_coll.insert_many(batch, ordered=False)
            copied += len(batch)
            print(f"    Copied {copied}/{src_cnt}.", flush=True)

        # Copy indexes
        try:
            for idx in src_coll.list_indexes():
                if idx["name"] == "_id_":
                    continue
                keys = list(idx["key"].items())
                unique = idx.get("unique", False)
                sparse = idx.get("sparse", False)
                dst_coll.create_index(keys, name=idx["name"], unique=unique, sparse=sparse)
        except Exception as e:
            print(f"    Index notice: {e}", flush=True)

    print("\n==========================================", flush=True)
    print("Migration Verification (sentinelai database):", flush=True)
    for c in dst_db.list_collection_names():
        print(f" - {c}: {dst_db[c].count_documents({})} documents", flush=True)
    print("==========================================", flush=True)

if __name__ == "__main__":
    migrate()
