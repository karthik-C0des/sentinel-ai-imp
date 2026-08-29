"""
Sentinel-AI: Indian Banking & Financial Cybercrime Synthetic Data Generation
Dynamically adapted for AML/Fraud Backend Compatibility
"""
import asyncio, os, random, uuid, math, logging
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Connections
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
AML_DB_NAME = os.getenv("DB_NAME", "threatsight360")
FRAUD_DB_NAME = "leafy_bank_bian"

# Indian Master Data
INDIAN_CITIES = [
    {"city": "Mumbai", "state": "Maharashtra", "state_code": "27", "lon": 72.8777, "lat": 19.0760, "pincode": "400001", "tier": 1},
    {"city": "Delhi", "state": "Delhi", "state_code": "07", "lon": 77.1025, "lat": 28.7041, "pincode": "110001", "tier": 1},
    {"city": "Bengaluru", "state": "Karnataka", "state_code": "29", "lon": 77.5946, "lat": 12.9716, "pincode": "560001", "tier": 1},
    {"city": "Hyderabad", "state": "Telangana", "state_code": "36", "lon": 78.4867, "lat": 17.3850, "pincode": "500001", "tier": 1},
    {"city": "Ahmedabad", "state": "Gujarat", "state_code": "24", "lon": 72.5714, "lat": 23.0225, "pincode": "380001", "tier": 1},
    {"city": "Chennai", "state": "Tamil Nadu", "state_code": "33", "lon": 80.2707, "lat": 13.0827, "pincode": "600001", "tier": 1},
    {"city": "Kolkata", "state": "West Bengal", "state_code": "19", "lon": 88.3639, "lat": 22.5726, "pincode": "700001", "tier": 1},
    {"city": "Pune", "state": "Maharashtra", "state_code": "27", "lon": 73.8567, "lat": 18.5204, "pincode": "411001", "tier": 1},
    {"city": "Surat", "state": "Gujarat", "state_code": "24", "lon": 72.8311, "lat": 21.1702, "pincode": "395003", "tier": 2}
]

INDIAN_BANKS = [
    {"bank": "State Bank of India", "code": "SBIN", "handles": ["@oksbi", "@sbi"]},
    {"bank": "HDFC Bank", "code": "HDFC", "handles": ["@okhdfcbank", "@hdfcbank"]},
    {"bank": "ICICI Bank", "code": "ICIC", "handles": ["@okicici", "@icici"]},
    {"bank": "Axis Bank", "code": "UTIB", "handles": ["@okaxis", "@axisbank"]}
]

INDIAN_MERCHANTS = {
    "grocery": ["Blinkit", "Zepto", "Instamart", "DMart Ready"],
    "restaurant": ["Zomato Online", "Swiggy Foods", "Haldiram's"],
    "retail": ["Tata CLiQ", "Reliance Digital", "Croma Electronics"],
    "online": ["Amazon India", "Flipkart Internet", "Myntra Designs"],
    "travel": ["MakeMyTrip", "IRCTC Rail", "IndiGo Airlines", "Uber India"]
}

FIRST_NAMES = ["Aarav", "Amit", "Rahul", "Priya", "Sneha", "Vikram", "Deepak", "Ananya", "Rajesh", "Sunita"]
LAST_NAMES = ["Sharma", "Patel", "Verma", "Gupta", "Singh", "Shah", "Mehta", "Kulkarni", "Iyer", "Nair"]

def generate_valid_pan(entity_type="individual", name=""):
    p1 = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=3))
    type_char = "P" if entity_type == "individual" else "C" if entity_type == "corporation" else "F"
    name_char = name.split()[-1][0].upper() if name else random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
    digits = f"{random.randint(1000, 9999)}"
    last_char = random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
    return f"{p1}{type_char}{name_char}{digits}{last_char}"

def generate_masked_aadhaar():
    return f"XXXX-XXXX-{random.randint(1000, 9999)}"

def generate_gstin(state_code, pan):
    return f"{state_code}{pan}1Z{random.choice('123456789ABCDEFGH')}"

def generate_ifsc(bank_code):
    return f"{bank_code}0{random.randint(100000, 999999)}"

def generate_npci_utr():
    return f"4{random.randint(1, 365):03d}{random.randint(10000000, 99999999)}"

def now(): return datetime.now(timezone.utc)
def rand_date(days_back=730): return now() - timedelta(days=random.randint(0, days_back))

def generate_customer_profiles():
    customers = []
    
    anchors = [
        {"entityId": "ENT-IN-2004", "name": "Amit Patel", "entityType": "individual", "category": "HIGH_RISK_INDIVIDUAL", "occupation": "Textile Trader", "city": "Surat", "riskScore": 88.0},
        {"entityId": "ENT-IN-2049", "name": "Mahadev Gaming Consultancy LLP", "entityType": "organization", "category": "SHELL_COMPANY", "occupation": "Software Consultancy", "city": "Mumbai", "riskScore": 92.0},
        {"entityId": "ENT-IN-2047", "name": "Navkar Bullion & Gold Traders", "entityType": "organization", "category": "PRECIOUS_METALS", "occupation": "Bullion Merchant", "city": "Ahmedabad", "riskScore": 86.0},
        {"entityId": "ENT-IN-2001", "name": "Aarav Sharma", "entityType": "individual", "category": "CUSTOMER", "occupation": "Software Architect", "city": "Bengaluru", "riskScore": 14.0},
        {"entityId": "ENT-IN-2005", "name": "Sneha Kulkarni", "entityType": "individual", "category": "CUSTOMER", "occupation": "Chartered Accountant", "city": "Pune", "riskScore": 12.0}
    ]
    
    for a in anchors:
        city_info = next(c for c in INDIAN_CITIES if c["city"] == a["city"])
        bank_info = random.choice(INDIAN_BANKS)
        pan = generate_valid_pan(a["entityType"], a["name"])
        aadhaar = generate_masked_aadhaar()
        gstin = generate_gstin(city_info["state_code"], pan) if a["entityType"] == "organization" else None
        
        # We must conform to the expected schema of the existing AML platform
        doc = {
            "entityId": a["entityId"],
            "entityType": a["entityType"],
            "name": {"full": a["name"], "aliases": [a["name"]]},
            "status": "under_review" if a["riskScore"] > 80 else "active",
            "addresses": [{
                "full": f"{random.randint(1,999)} Station Road, {a['city']}, IN",
                "city": a["city"],
                "country": "IN",
                "type": "residential" if a["entityType"] == "individual" else "business",
                "primary": True,
                "verified": True,
                "validFrom": rand_date(1800).isoformat()
            }],
            "identifiers": [
                {"type": "pan", "value": pan, "country": "IN", "verified": True},
                {"type": "aadhaar", "value": aadhaar, "country": "IN", "verified": True}
            ],
            "nationality": "IN",
            "residency": "IN",
            "riskAssessment": {
                "overall": {"score": a["riskScore"], "level": "critical" if a["riskScore"] > 80 else "low"},
                "factors": {"geographic": 10, "transaction": random.randint(10, 90), "network": random.randint(10, 90), "watchlist": 0}
            },
            "customerInfo": {"businessType": a["occupation"], "accountOpenDate": rand_date(1800).isoformat()},
            "watchlistFlags": {"isOnWatchlist": False, "matches": []},
            
            # Embeddings fixed to 384 dimensions!
            "identifierEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "behavioralEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "profileEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "embedding": [],
            "createdAt": rand_date(1800).isoformat(),
            "updatedAt": rand_date(30).isoformat(),
        }
        if gstin:
            doc["identifiers"].append({"type": "gstin", "value": gstin, "country": "IN", "verified": True})
        
        customers.append(doc)
        
    for i in range(60, 110):
        eid = f"ENT-IN-20{i:02d}"
        is_corp = (i % 4 == 0)
        etype = "organization" if is_corp else "individual"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" if not is_corp else f"{random.choice(['Vanguard', 'Apex', 'Shree', 'Surya'])} {random.choice(['Logistics', 'Enterprises', 'Ventures'])} Pvt Ltd"
        city_info = random.choice(INDIAN_CITIES)
        pan = generate_valid_pan(etype, name)
        risk_score = round(random.uniform(8.0, 35.0), 1) if (i % 5 != 0) else round(random.uniform(72.0, 94.0), 1)
        
        doc = {
            "entityId": eid,
            "entityType": etype,
            "name": {"full": name, "aliases": [name]},
            "status": "under_review" if risk_score > 80 else "active",
            "addresses": [{
                "full": f"{random.randint(1,999)} Main Road, {city_info['city']}, IN",
                "city": city_info["city"],
                "country": "IN",
                "type": "residential" if not is_corp else "business",
                "primary": True,
                "verified": True,
                "validFrom": rand_date(1800).isoformat()
            }],
            "identifiers": [
                {"type": "pan", "value": pan, "country": "IN", "verified": True},
                {"type": "aadhaar", "value": generate_masked_aadhaar(), "country": "IN", "verified": True}
            ],
            "nationality": "IN",
            "residency": "IN",
            "riskAssessment": {
                "overall": {"score": risk_score, "level": "high" if risk_score > 70 else "low"},
                "factors": {"geographic": 10, "transaction": random.randint(10, 90), "network": random.randint(10, 90), "watchlist": 0}
            },
            "customerInfo": {"businessType": "Trade" if is_corp else "Salaried", "accountOpenDate": rand_date(1800).isoformat()},
            "watchlistFlags": {"isOnWatchlist": False, "matches": []},
            
            # Embeddings fixed to 384 dimensions
            "identifierEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "behavioralEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "profileEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "embedding": [],
            "createdAt": rand_date(1800).isoformat(),
            "updatedAt": rand_date(30).isoformat(),
        }
        customers.append(doc)
        
    # Ensure specific targets used in demo scenarios exist in DB
    demo_targets = [
        {"name": "Aarav Sharma", "type": "individual"},
        {"name": "Priya Patel", "type": "individual"},
        {"name": "Sneha Verma", "type": "individual"},
        {"name": "Amit Gupta", "type": "individual"},
        {"name": "Amit K Gupta", "type": "individual"},
        {"name": "Ananya Singh", "type": "individual"},
        {"name": "Summit Investments India Pvt Ltd", "type": "organization"},
        {"name": "BrotSequi Traders", "type": "organization"},
        {"name": "Zorbach Holdings Pvt Ltd", "type": "organization"},
        {"name": "NoneAbandonner India", "type": "organization"},
        {"name": "Reliance Logistics Holdings", "type": "organization"},
        {"name": "Deploy Trading Corp India", "type": "organization"},
        {"name": "Rajesh Mehta", "type": "individual"},
        {"name": "Sunita Kulkarni", "type": "individual"},
        {"name": "Vikram Iyer", "type": "individual"},
    ]
    
    for idx, target in enumerate(demo_targets):
        doc = {
            "entityId": f"ENT-DEMO-{idx:03d}",
            "entityType": target["type"],
            "name": {"full": target["name"], "aliases": [target["name"]]},
            "status": "active",
            "addresses": [{
                "full": f"{random.randint(1,999)} Demo Road, Mumbai, IN",
                "city": "Mumbai",
                "country": "IN",
                "type": "residential" if target["type"] == "individual" else "business",
                "primary": True,
                "verified": True,
                "validFrom": rand_date(1800).isoformat()
            }],
            "identifiers": [
                {"type": "pan", "value": generate_valid_pan(target["type"], target["name"]), "country": "IN", "verified": True}
            ],
            "nationality": "IN",
            "residency": "IN",
            "riskAssessment": {
                "overall": {"score": 50, "level": "medium"},
                "factors": {"geographic": 10, "transaction": 50, "network": 50, "watchlist": 0}
            },
            "customerInfo": {"businessType": "Trade" if target["type"] == "organization" else "Salaried", "accountOpenDate": rand_date(1800).isoformat()},
            "watchlistFlags": {"isOnWatchlist": False, "matches": []},
            "identifierEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "behavioralEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "profileEmbedding": [random.uniform(-1, 1) for _ in range(384)],
            "embedding": [],
            "createdAt": rand_date(1800).isoformat(),
            "updatedAt": rand_date(30).isoformat(),
        }
        customers.append(doc)

    return customers

def generate_transactions(customers_docs, total_count=10000):
    txns = []
    
    entity_map = {c["entityId"]: c for c in customers_docs}
    
    logger.info("Synthesizing Rule 114B PAN Structuring transactions...")
    for i in range(1200):
        src = entity_map.get("ENT-IN-2004", customers_docs[0])
        tgt = entity_map.get("ENT-IN-2049", customers_docs[1])
        amt = round(random.uniform(48200.0, 49950.0), 2)
        tx_id = f"TXN-IN-STRUC-{100000 + i}"
        
        # Compliant to the expected transactionsv2 format
        tx = {
            "transactionId": tx_id,
            "entityId": src["entityId"],
            "counterpartyEntityId": tgt["entityId"],
            "amount": amt,
            "currency": "INR",
            "type": "upi_transfer",
            "direction": "outgoing",
            "timestamp": rand_date(45).isoformat(),
            "description": "UPI Settlement",
            "flagged": True,
            "createdAt": now().isoformat(),
            "location": {"type": "Point", "coordinates": [72.8311, 21.1702]}
        }
        txns.append(tx)
        
    logger.info("Synthesizing PMLA Section 12 CTR Cash Transactions...")
    for i in range(1200, 2200):
        src = entity_map.get("ENT-IN-2004", customers_docs[0])
        amt = round(random.uniform(1050000.0, 3200000.0), 2)
        tx_id = f"TXN-IN-CTR-{100000 + i}"
        
        tx = {
            "transactionId": tx_id,
            "entityId": src["entityId"],
            "counterpartyEntityId": "ENT-IN-BANK",
            "amount": amt,
            "currency": "INR",
            "type": "cash_deposit",
            "direction": "incoming",
            "timestamp": rand_date(120).isoformat(),
            "description": "Branch Cash Deposit",
            "flagged": True,
            "createdAt": now().isoformat(),
            "location": {"type": "Point", "coordinates": [72.8311, 21.1702]}
        }
        txns.append(tx)
        
    logger.info(f"Synthesizing {total_count - len(txns)} routine domestic banking transactions...")
    for i in range(len(txns), total_count):
        src = random.choice(customers_docs)
        tgt = random.choice([c for c in customers_docs if c["entityId"] != src["entityId"]])
        rail = random.choice(["upi_transfer", "internal_transfer", "wire_transfer"])
        amt = round(random.uniform(35.0, 2800.0), 2)
        tx_id = f"TXN-IN-{100000 + i}"
        
        tx = {
            "transactionId": tx_id,
            "entityId": src["entityId"],
            "counterpartyEntityId": tgt["entityId"],
            "amount": amt,
            "currency": "INR",
            "type": rail,
            "direction": random.choice(["incoming", "outgoing"]),
            "timestamp": rand_date(180).isoformat(),
            "description": "Domestic transaction",
            "flagged": False,
            "createdAt": now().isoformat(),
        }
        txns.append(tx)
        
    return txns

def generate_relationships():
    # Compliant to threatsightRelationships format (source.entityId)
    return [
        {"relationshipId": "REL-IN-401", "source": {"entityId": "ENT-IN-2004", "entityType": "individual"}, "target": {"entityId": "ENT-IN-2049", "entityType": "organization"}, "type": "owner_of", "direction": "directed", "strength": 0.98, "active": True},
        {"relationshipId": "REL-IN-402", "source": {"entityId": "ENT-IN-2049", "entityType": "organization"}, "target": {"entityId": "ENT-IN-2047", "entityType": "organization"}, "type": "subsidiary_of", "direction": "directed", "strength": 0.96, "active": True},
        {"relationshipId": "REL-IN-403", "source": {"entityId": "ENT-IN-2004", "entityType": "individual"}, "target": {"entityId": "ENT-IN-2060", "entityType": "organization"}, "type": "director_of", "direction": "directed", "strength": 0.95, "active": True},
    ]

def normalize_vector(v):
    norm = math.sqrt(sum(x*x for x in v))
    return [x/norm for x in v] if norm > 0 else v

def generate_fraud_patterns():
    # Generate 384-dim embeddings instead of 1536
    return [
        {"pattern_name": "Rule 114B PAN Structuring", "description": "Series of deposits structured between Rs. 48,000 and Rs. 49,950 avoiding PAN quoting", "severity": "high", "vector_embedding": normalize_vector([random.gauss(0, 1) for _ in range(384)])},
        {"pattern_name": "UPI Mule Ring Fan-out", "description": "Rapid inflow of UPI transfers from multiple accounts followed by immediate ATM liquidation", "severity": "high", "vector_embedding": normalize_vector([random.gauss(0, 1) for _ in range(384)])},
        {"pattern_name": "Digital Arrest Cyber Scam", "description": "Uncharacteristic high-value overnight RTGS transfer (IT Act 66D) to dummy corporate account", "severity": "high", "vector_embedding": normalize_vector([random.gauss(0, 1) for _ in range(384)])},
        {"pattern_name": "PMLA CTR Large Cash Inflow", "description": "Branch cash deposits exceeding statutory Rs. 10 Lakhs threshold", "severity": "medium", "vector_embedding": normalize_vector([random.gauss(0, 1) for _ in range(384)])},
        {"pattern_name": "Shell Entity Hawala Layering", "description": "Circular fund transfers through commercial LLPs without clear economic substance", "severity": "high", "vector_embedding": normalize_vector([random.gauss(0, 1) for _ in range(384)])}
    ]

async def generate():
    aml_client = AsyncIOMotorClient(MONGODB_URI)
    aml_db = aml_client[AML_DB_NAME]
    
    fraud_client = AsyncIOMotorClient(MONGODB_URI)
    fraud_db = fraud_client[FRAUD_DB_NAME]

    logger.info("Generating Indian Entity profiles...")
    entities = generate_customer_profiles()
    await aml_db["threatsightEntities"].drop()
    await aml_db["threatsightEntities"].insert_many(entities)
    print(f"  entities: {len(entities)}")

    logger.info("Generating AML transactions...")
    await aml_db["transactionsv2"].drop()
    txns = generate_transactions(entities)
    await aml_db["transactionsv2"].insert_many(txns)
    print(f"  transactionsv2: {len(txns)}")

    logger.info("Generating multi-hop relationships...")
    await aml_db["threatsightRelationships"].drop()
    rels = generate_relationships()
    await aml_db["threatsightRelationships"].insert_many(rels)
    print(f"  relationships: {len(rels)}")

    logger.info("Generating fraud patterns (384-dim embeddings)...")
    await aml_db["fraud_patterns"].drop()
    patterns = generate_fraud_patterns()
    await aml_db["fraud_patterns"].insert_many(patterns)
    print(f"  fraud_patterns: {len(patterns)}")

    logger.info("Setting up Indexes...")
    await aml_db["threatsightEntities"].create_index("entityId", unique=True)
    await aml_db["transactionsv2"].create_index("transactionId", unique=True)
    await aml_db["transactionsv2"].create_index("entityId")
    await aml_db["threatsightRelationships"].create_index("relationshipId", unique=True)
    await aml_db["threatsightRelationships"].create_index("source.entityId")

    aml_client.close()
    fraud_client.close()
    
    print("\n  DONE! Indian dataset generated safely.")

if __name__ == "__main__":
    asyncio.run(generate())
