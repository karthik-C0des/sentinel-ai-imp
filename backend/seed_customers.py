"""
Seed script — inserts 20 demo customers into `leafy_bank_bian.customers`
stamped with sourceSystem=threatsight360 so the fraud backend's scoped()
filter finds them and the Transaction Simulator dropdown populates.

Usage (from the repo root):
    cd backend
    poetry run python seed_customers.py
"""

import asyncio, os, random, uuid
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
# The fraud backend's customer.py hardcodes leafy_bank_bian as its default DB,
# regardless of DB_NAME in .env (which points to threatsight360 for the AML backend).
DB_NAME     = "leafy_bank_bian"
COLLECTION  = "customers"
SOURCE      = "threatsight360"

# ── helpers ──────────────────────────────────────────────────────────────────
def now():
    return datetime.now(timezone.utc).isoformat()

def rand_date(days_back: int = 1800) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_back))).isoformat()

FIRST  = ["James","Maria","Chen","Ahmed","Sofia","Robert","Priya","Carlos","Anna","Michael",
          "Fatima","Luca","Yuki","David","Amara","Hassan","Elena","Marco","Nadia","Patrick"]
LAST   = ["Smith","Santos","Wang","Al-Rashid","Mueller","Johnson","Patel","Rodriguez",
          "Fischer","Okafor","Nguyen","Rossi","Tanaka","Brown","Diallo","Hassan",
          "Petrova","Bianchi","Kim","Williams"]
CITIES = [
    ("New York","NY","US",[-73.9857,40.7484]),
    ("Los Angeles","CA","US",[-118.2437,34.0522]),
    ("London","ENG","GB",[-0.1276,51.5074]),
    ("Singapore","SG","SG",[103.8198,1.3521]),
    ("Dubai","DU","AE",[55.2708,25.2048]),
    ("Zurich","ZH","CH",[8.5417,47.3769]),
    ("Toronto","ON","CA",[-79.3832,43.6532]),
    ("Sydney","NSW","AU",[151.2093,-33.8688]),
]
CATEGORIES  = ["retail","restaurant","grocery","gas","healthcare","utilities","entertainment","travel","money_transfer"]
DEVICES     = [
    {"type":"mobile","os":"iOS","browser":"Safari"},
    {"type":"mobile","os":"Android","browser":"Chrome"},
    {"type":"laptop","os":"Windows","browser":"Chrome"},
    {"type":"laptop","os":"macOS","browser":"Safari"},
    {"type":"tablet","os":"iPadOS","browser":"Safari"},
]
SCENARIOS   = ["normal_spending","high_value","travel_heavy","small_frequent","mixed_risk"]


def make_customer(idx: int) -> dict:
    first  = random.choice(FIRST)
    last   = random.choice(LAST)
    risk   = random.randint(5, 90)
    city, state, country, coords = random.choice(CITIES)
    dev    = random.choice(DEVICES)
    cats   = random.sample(CATEGORIES, k=random.randint(2, 4))
    avg_amt = round(random.uniform(50, 3000), 2)
    scenario = random.choice(SCENARIOS)

    return {
        "customerId":   f"SEED-{idx:03d}-{uuid.uuid4().hex[:6].upper()}",
        "sourceSystem": SOURCE,
        "identification": {
            "legalName":   f"{first} {last}",
            "firstName":   first,
            "lastName":    last,
            "dateOfBirth": rand_date(20000),
            "nationality": country,
        },
        "identifiers": [
            {
                "type":     "accountNumber",
                "value":    f"ACC{random.randint(10_000_000_000, 99_999_999_999)}",
                "country":  country,
                "verified": True,
            }
        ],
        "contact": {
            "email": f"{first.lower()}.{last.lower()}{idx}@demo.example.com",
            "phone": f"+1-555-{random.randint(1000, 9999)}",
            "address": {"city": city, "state": state, "country": country},
        },
        "riskProfile": {
            "overall": {
                "score": risk,
                "level": "low" if risk < 30 else "medium" if risk < 60 else "high" if risk < 80 else "critical",
                "trend": random.choice(["stable","worsening","improving"]),
            },
            "assessedAt": now(),
            "history": [],
        },
        "behavioralProfile": {
            "source": "fraud",
            "devices": [
                {
                    "device_id": str(uuid.uuid4()),
                    "type": dev["type"],
                    "os":   dev["os"],
                    "browser": dev["browser"],
                    "ip_range": [f"192.168.{random.randint(1,254)}.0/24"],
                    "usual_locations": [
                        {
                            "city": city, "state": state, "country": country,
                            "location": {"type": "Point", "coordinates": [
                                coords[0] + random.uniform(-0.5, 0.5),
                                coords[1] + random.uniform(-0.5, 0.5),
                            ]},
                            "frequency": round(random.uniform(0.5, 1.0), 2),
                        }
                    ],
                }
            ],
            "transaction_patterns": {
                "avg_transaction_amount": avg_amt,
                "std_transaction_amount": round(avg_amt * random.uniform(0.1, 0.4), 2),
                "avg_transactions_per_day": round(random.uniform(0.5, 5.0), 2),
                "common_merchant_categories": cats,
                "usual_transaction_locations": [
                    {
                        "city": city, "state": state, "country": country,
                        "location": {"type": "Point", "coordinates": coords},
                        "frequency": round(random.uniform(0.6, 1.0), 2),
                    }
                ],
            },
            "location_patterns": [
                {
                    "city": city, "state": state, "country": country,
                    "location": {"type": "Point", "coordinates": coords},
                    "frequency": round(random.uniform(0.6, 1.0), 2),
                }
            ],
            "ip_addresses": [],
        },
        "screening": {
            "scenarioKey": scenario,
            "sourceSystem": SOURCE,
        },
        "status":  "active",
        "type":    random.choice(["individual","business"]),
        "segment": random.choice(["retail","premium","corporate"]),
        "createdAt": rand_date(730),
        "updatedAt": now(),
    }


async def seed():
    print(f"Connecting to MongoDB...  DB={DB_NAME}  collection={COLLECTION}")
    client = AsyncIOMotorClient(MONGODB_URI)
    col    = client[DB_NAME][COLLECTION]

    # Delete any previous seed docs so re-running is always safe
    del_result = await col.delete_many({"sourceSystem": SOURCE, "customerId": {"$regex": "^SEED-"}})
    if del_result.deleted_count:
        print(f"  Removed {del_result.deleted_count} existing seed docs.")

    customers = [make_customer(i) for i in range(1, 21)]
    result    = await col.insert_many(customers)
    print(f"  OK: Inserted {len(result.inserted_ids)} customers into {DB_NAME}.{COLLECTION}")

    # Quick verification
    count = await col.count_documents({"sourceSystem": SOURCE})
    print(f"  Total threatsight360 customers now: {count}")
    client.close()
    print("\nDone! Refresh the Transaction Simulator - the Entity dropdown should now populate.")


if __name__ == "__main__":
    asyncio.run(seed())
