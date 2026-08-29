"""
ThreatSight 360 - Demo Data Generator
"""
import asyncio, os, random, logging
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "threatsight360")

def now(): return datetime.now(timezone.utc)
def rand_date(days_back=730): return now() - timedelta(days=random.randint(0, days_back))
def rand_amount(lo=100, hi=500_000): return round(random.uniform(lo, hi), 2)

COUNTRIES = ["US","GB","DE","SG","AE","CH","KY","BVI","PA","MX","BR","CN","IN","NG","ZA"]
FIRST_NAMES = ["James","Maria","Chen","Ahmed","Sofia","Robert","Priya","Carlos","Anna","Michael","Fatima","Luca","Yuki","David","Amara","Hassan","Elena","Marco","Nadia","Patrick"]
LAST_NAMES = ["Smith","Santos","Wang","Al-Rashid","Mueller","Johnson","Patel","Rodriguez","Fischer","Okafor","Nguyen","Rossi","Tanaka","Brown","Diallo","Hassan","Petrova","Bianchi","Kim","Williams"]
ORG_NAMES = ["Global Holdings Ltd","Pacific Trading LLC","Atlantic Capital Group","Summit Investments Inc","Apex Ventures Corp","Prime Finance SA","Delta Assets BV","Sigma Consulting Ltd","Alpha Resources PLC","Nexus Solutions GmbH","Meridian Trust Co","Vanguard Capital Ltd","Sterling Trade Inc","Horizon Finance Group","Cascade Holdings BV"]
CITIES = ["New York","London","Singapore","Dubai","Zurich","Panama City","George Town","Hong Kong","Lagos","Sao Paulo","Mumbai","Shanghai","Toronto","Sydney","Johannesburg"]
TX_TYPES = ["wire_transfer","cash_deposit","ach_transfer","check","internal_transfer","crypto_conversion","trade_finance"]
REL_TYPES = ["director_of","owner_of","subsidiary_of","family_member","same_address","frequent_transactor","beneficiary","suspicious_link"]

def make_entity(i, entity_type="individual"):
    eid = f"ENT-{i:04d}"
    risk_score = random.randint(5, 95)
    risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high" if risk_score < 80 else "critical"
    nationality = random.choice(COUNTRIES)
    country = random.choice(COUNTRIES)
    city = random.choice(CITIES)
    watchlisted = risk_score > 80 and random.random() < 0.3
    
    # Define status based on risk and watchlist
    if watchlisted or risk_level in ["high", "critical"]:
        status = "under_review"
    elif risk_score < 20:
        status = "inactive"
    else:
        status = "active"

    if entity_type == "individual":
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"
        aliases = [f"{first[0]}. {last}", f"{first} {last[:3]}."]
        btype = None
    else:
        full_name = random.choice(ORG_NAMES) + f" {i}"
        aliases = [full_name.split()[0] + " " + full_name.split()[1]]
        btype = random.choice(["financial_services","real_estate","trading","consulting","technology","import_export"])
    doc = {
        "entityId": eid, "entityType": entity_type,
        "name": {"full": full_name, "aliases": aliases},
        "status": status,
        "addresses": [{
            "full": f"{random.randint(1,9999)} Main St, {city}, {country}", 
            "city": city, 
            "country": country, 
            "type": "residential",
            "primary": True,
            "verified": random.random() > 0.3,
            "validFrom": rand_date(1800).isoformat()
        }],
        "identifiers": [{
            "type": random.choice(["passport","national_id","tax_id","company_reg"]), 
            "value": f"{nationality}-{random.randint(10000000,99999999)}", 
            "country": nationality,
            "issueDate": rand_date(1800).isoformat(),
            "expiryDate": (now() + timedelta(days=random.randint(30, 3650))).isoformat(),
            "verified": random.random() > 0.2
        }],
        "nationality": nationality, "residency": country,
        "riskAssessment": {"overall": {"score": risk_score, "level": risk_level}, "factors": {"geographic": random.randint(0,100), "transaction": random.randint(0,100), "network": random.randint(0,100), "watchlist": 100 if watchlisted else 0}},
        "customerInfo": {"businessType": btype, "accountOpenDate": rand_date(1800).isoformat()},
        "watchlistFlags": {"isOnWatchlist": watchlisted, "matches": [{"list": "OFAC-SDN", "matchScore": round(random.uniform(0.8,1.0),2)}] if watchlisted else []},
        "identifierEmbedding": [random.uniform(-1, 1) for _ in range(384)],
        "behavioralEmbedding": [random.uniform(-1, 1) for _ in range(384)],
        "profileEmbedding": [random.uniform(-1, 1) for _ in range(384)], # Legacy
        "embedding": [], "createdAt": rand_date(1800).isoformat(), "updatedAt": rand_date(30).isoformat(),
    }
    if entity_type == "individual":
        doc["name"]["first"] = full_name.split()[0]; doc["name"]["last"] = full_name.split()[-1]
    return doc

def make_txnv2(i, entity_ids):
    eid = random.choice(entity_ids); cp = random.choice([e for e in entity_ids if e != eid])
    amount = rand_amount()
    return {"transactionId": f"TXNV2-{i:06d}", "entityId": eid, "counterpartyEntityId": cp, "amount": amount, "currency": random.choice(["USD","EUR","GBP","AED","CHF","SGD"]), "type": random.choice(TX_TYPES), "direction": random.choice(["incoming","outgoing"]), "timestamp": rand_date(720).isoformat(), "description": random.choice(["International wire transfer","Business payment","Investment transfer","Trade settlement","Consulting fee","Dividend payment","Capital contribution"]), "flagged": amount > 100_000 or random.random() < 0.08, "createdAt": now().isoformat()}

def make_rel(i, entity_ids, entity_map):
    src = random.choice(entity_ids); tgt = random.choice([e for e in entity_ids if e != src])
    rt = random.choice(REL_TYPES)
    return {"relationshipId": f"REL-{i:04d}", "source": {"entityId": src, "entityType": entity_map[src]}, "target": {"entityId": tgt, "entityType": entity_map[tgt]}, "type": rt, "direction": "directed", "strength": round(random.uniform(0.3,1.0),2), "confidence": round(random.uniform(0.6,1.0),2), "active": True, "verified": rt != "suspicious_link", "evidence": ["transaction_pattern"], "datasource": "internal_analysis", "createdAt": rand_date(600).isoformat(), "updatedAt": rand_date(30).isoformat()}

def make_customer(i):
    first = random.choice(FIRST_NAMES); last = random.choice(LAST_NAMES); risk = random.randint(5,90)
    return {"customer_id": f"CUST-{i:03d}", "personal_info": {"name": f"{first} {last}", "email": f"{first.lower()}.{last.lower()}{i}@example.com", "phone": f"+1-555-{random.randint(1000,9999)}"}, "account_info": {"account_type": random.choice(["checking","savings","business"]), "opened_date": rand_date(1800).isoformat(), "status": "active"}, "device_fingerprints": [{"device_id": f"DEV-{i}-1", "type": "mobile", "os": "iOS"}], "usual_locations": {"type": "MultiPoint", "coordinates": [[-73.9857+random.uniform(-5,5), 40.7484+random.uniform(-5,5)]]}, "transaction_behavior": {"avg_amount": round(random.uniform(50,2000),2), "typical_categories": ["grocery","gas","dining"], "usual_times": {"start": 8, "end": 22}}, "risk_profile": {"score": risk, "level": "low" if risk<30 else "medium" if risk<60 else "high", "flags": []}}

def make_fraud_txn(i, customer_ids):
    cid = random.choice(customer_ids); amount = rand_amount(10,5000); risk = random.randint(5,95)
    return {"transaction_id": f"TXN-{i:06d}", "sourceSystem": "threatsight360", "customer_id": cid, "type": random.choice(["purchase","atm_withdrawal","online_transfer","bill_payment"]), "amount": amount, "merchant": {"name": random.choice(["Amazon","Walmart","Shell","Best Buy","CVS"]), "category": random.choice(["retail","gas","electronics","pharmacy"]), "location": {"type": "Point", "coordinates": [-73.9857+random.uniform(-10,10), 40.7484+random.uniform(-10,10)]}}, "device": {"device_id": f"DEV-{random.randint(1,50)}-1", "type": "mobile"}, "timestamp": rand_date(365).isoformat(), "risk_assessment": {"score": risk, "level": "low" if risk<30 else "medium" if risk<60 else "high" if risk<80 else "critical", "flags": (["unusual_amount"] if amount>2000 else []), "factor_scores": {"amount": random.randint(0,100), "location": random.randint(0,100), "device": random.randint(0,100), "velocity": random.randint(0,100), "pattern": random.randint(0,100)}}, "vector_embedding": [random.uniform(-1, 1) for _ in range(384)]}

FRAUD_PATTERNS = [
    {"name":"Account Takeover","description":"Unauthorized access involving sudden device/location changes followed by high-value transfers.","indicators":["new_device","password_change","high_amount"],"risk_level":"critical","vector_embedding":[random.uniform(-1, 1) for _ in range(384)]},
    {"name":"Structuring","description":"Multiple deposits just below $10,000 CTR threshold.","indicators":["near_threshold_deposits","multiple_accounts","same_day"],"risk_level":"high","vector_embedding":[random.uniform(-1, 1) for _ in range(384)]},
    {"name":"Card Not Present Fraud","description":"Fraudulent online purchases using stolen card credentials.","indicators":["new_merchant","geo_mismatch","high_velocity"],"risk_level":"high","vector_embedding":[random.uniform(-1, 1) for _ in range(384)]},
    {"name":"Synthetic Identity","description":"Combination of real and fabricated PII to create a new identity.","indicators":["thin_file","inconsistent_pii","rapid_credit_seeking"],"risk_level":"critical","vector_embedding":[random.uniform(-1, 1) for _ in range(384)]},
    {"name":"Money Mule","description":"Third-party account used to receive and forward fraudulent funds.","indicators":["sudden_large_deposit","immediate_withdrawal","multiple_senders"],"risk_level":"high","vector_embedding":[random.uniform(-1, 1) for _ in range(384)]},
]

async def generate():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    BATCH = 500

    logger.info("Generating 504 entities...")
    entities = [make_entity(i, "individual") for i in range(1,341)] + [make_entity(i, "organization") for i in range(341,505)]
    random.shuffle(entities)
    await db["threatsightEntities"].drop()
    await db["threatsightEntities"].insert_many(entities)
    print(f"  entities: {len(entities)}")

    entity_ids = [e["entityId"] for e in entities]
    entity_map = {e["entityId"]: e["entityType"] for e in entities}

    logger.info("Generating 12,766 AML transactions...")
    await db["transactionsv2"].drop()
    total = 0
    for start in range(1, 12767, BATCH):
        batch = [make_txnv2(i, entity_ids) for i in range(start, min(start+BATCH, 12767))]
        await db["transactionsv2"].insert_many(batch); total += len(batch)
    print(f"  transactionsv2: {total}")

    logger.info("Generating 519 relationships...")
    await db["threatsightRelationships"].drop()
    rels = [make_rel(i, entity_ids, entity_map) for i in range(1,520)]
    await db["threatsightRelationships"].insert_many(rels)
    print(f"  relationships: {len(rels)}")

    logger.info("Generating 50 customers...")
    await db["customers"].drop()
    customers = [make_customer(i) for i in range(1,51)]
    await db["customers"].insert_many(customers)
    print(f"  customers: {len(customers)}")
    cids = [c["customer_id"] for c in customers]

    logger.info("Generating 26,000 fraud transactions...")
    await db["transactions"].drop()
    total = 0
    for start in range(1, 26001, BATCH):
        batch = [make_fraud_txn(i, cids) for i in range(start, min(start+BATCH, 26001))]
        await db["transactions"].insert_many(batch); total += len(batch)
    print(f"  fraud transactions: {total}")

    await db["fraud_patterns"].drop()
    await db["fraud_patterns"].insert_many(FRAUD_PATTERNS)
    print(f"  fraud_patterns: {len(FRAUD_PATTERNS)}")

    await db["threatsightEntities"].create_index("entityId", unique=True)
    await db["threatsightEntities"].create_index("entityType")
    await db["transactionsv2"].create_index("transactionId", unique=True)
    await db["transactionsv2"].create_index("entityId")
    await db["threatsightRelationships"].create_index("relationshipId", unique=True)
    await db["threatsightRelationships"].create_index("source.entityId")
    await db["customers"].create_index("customer_id", unique=True)
    await db["transactions"].create_index("transaction_id", unique=True)
    await db["transactions"].create_index("customer_id")
    client.close()
    print("\n  DONE! All data generated successfully.")

asyncio.run(generate())
