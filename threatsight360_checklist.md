# ✅ ThreatSight 360 — M10 Setup, Terminate & Recovery Checklist

> **Strategy:** Setup M10 → Test → Terminate cluster to save cost → Recover before Presentation Day

---

## 📦 PHASE 1 — INITIAL M10 SETUP

### 🗄️ Step 1: MongoDB Atlas — Create M10 Cluster

- [ ] Sign up / log in at [cloud.mongodb.com](https://cloud.mongodb.com)
- [ ] Create a new **Project** (e.g. `ThreatSight360`)
- [ ] Create a new cluster → select **M10 tier**
- [ ] Region: choose closest to your location (e.g. `ap-south-1` for India)
- [ ] Set cluster name (e.g. `threatsight-cluster`)
- [ ] Create a **Database User**:
  - Username: _(note it down)_ → `__________________`
  - Password: _(note it down)_ → `__________________`
  - Role: `Atlas admin`
- [ ] Add your IP to **Network Access** (or allow `0.0.0.0/0` for dev)
- [ ] Click **Connect** → **Drivers** → Copy the connection string
  - Save it: `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/`
  - Saved URI: `__________________`

---

### 🔍 Step 2: MongoDB Atlas — Create Search Indexes

> ⚠️ All index names must match EXACTLY

#### Vector Search Indexes (Atlas UI → Search → Create Index → JSON Editor)

- [ ] **`transaction_vector_index`** on collection `transactions`
  ```json
  {
    "mappings": {
      "dynamic": true,
      "fields": {
        "vector_embedding": {
          "type": "knnVector",
          "dimensions": 1536,
          "similarity": "cosine"
        }
      }
    }
  }
  ```

- [ ] **`entity_vector_search_index`** on collection `entities`
  ```json
  {
    "type": "vectorSearch",
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 1536,
        "similarity": "cosine"
      }
    ]
  }
  ```

#### Atlas Search Indexes (Atlas UI → Search → Create Index → JSON Editor)

- [ ] **`entity_resolution_search`** on collection `entities`
  _(Full JSON in README.md → "Entity Resolution Search Index" section)_

- [ ] **`entity_text_search_index`** on collection `entities`
  _(Full JSON in README.md → "Entity Text Search Index" section)_

---

### ☁️ Step 3: AWS Bedrock Setup

- [ ] Log in to [aws.amazon.com/console](https://aws.amazon.com/console)
- [ ] Go to **Bedrock** → **Model Access** → Request access:
  - [ ] `Claude Haiku 4.5` (or latest Haiku)
  - [ ] `Amazon Titan Text Embeddings V2`
- [ ] Go to **IAM** → **Users** → Create user with programmatic access
  - Attach policy: `AmazonBedrockFullAccess`
  - Save:
    - `AWS_ACCESS_KEY_ID` → `__________________`
    - `AWS_SECRET_ACCESS_KEY` → `__________________`
    - `AWS_REGION` → `us-east-1`

---

### 🚢 Step 4: Voyage AI API Key

- [ ] Sign up at [voyageai.com](https://www.voyageai.com)
- [ ] Get API key from dashboard
  - `VOYAGE_API_KEY` → `__________________`

---

### ⚙️ Step 5: Configure Environment Files

- [ ] **`backend/.env`** — copy from `.env.example` and fill in:
  ```
  MONGODB_URI=<your_uri>
  DB_NAME=fsi-threatsight360
  AWS_ACCESS_KEY_ID=<key>
  AWS_SECRET_ACCESS_KEY=<secret>
  AWS_REGION=us-east-1
  HOST=0.0.0.0
  PORT=8000
  FRONTEND_URL=http://localhost:3000
  ```

- [ ] **`aml-backend/.env`** — copy from `.env.example` and fill in:
  ```
  MONGODB_URI=<your_uri>
  DB_NAME=fsi-threatsight360
  AWS_ACCESS_KEY_ID=<key>
  AWS_SECRET_ACCESS_KEY=<secret>
  AWS_REGION=us-east-1
  HOST=0.0.0.0
  PORT=8001
  FRONTEND_URL=http://localhost:3000
  ATLAS_SEARCH_INDEX=entity_resolution_search
  ENTITY_VECTOR_INDEX=entity_vector_search_index
  VOYAGE_API_KEY=<voyage_key>
  ```

- [ ] **`frontend/.env.local`** — create with:
  ```
  NEXT_PUBLIC_FRAUD_API_URL=http://localhost:8000
  NEXT_PUBLIC_AML_API_URL=http://localhost:8001
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```

---

### 📦 Step 6: Install Dependencies

```powershell
# Backend (Fraud)
cd backend
poetry install

# AML Backend
cd ..\aml-backend
poetry install

# Frontend
cd ..\frontend
npm install
```

- [ ] `backend` dependencies installed
- [ ] `aml-backend` dependencies installed
- [ ] `frontend` dependencies installed

---

### 🌱 Step 7: Seed the Database

- [ ] Run **Transaction Data** notebook (generates 50 customers + 26,000 transactions):
  ```powershell
  jupyter notebook "docs/ThreatSight360 - Transaction Synthetic Data Generation.ipynb"
  ```

- [ ] Run **Entity Data** notebook (generates ~504 entities + ~519 relationships):
  ```powershell
  jupyter notebook "docs/ThreatSight 360 - Entity Resolution Synthetic Data Generation.ipynb"
  ```

- [ ] Seed **Typology Library** (12 AML typologies via API):
  ```powershell
  # With all backends running:
  Invoke-RestMethod -Method POST http://localhost:8001/agents/seed
  ```

- [ ] Verify data in Atlas UI:
  - [ ] `customers` → ~50 documents
  - [ ] `transactions` → ~26,000 documents
  - [ ] `fraud_patterns` → ~5 documents
  - [ ] `entities` → ~504 documents
  - [ ] `relationships` → ~519 documents
  - [ ] `transactionsv2` → ~12,766 documents
  - [ ] `typology_library` → 12 documents
  - [ ] `compliance_policies` → 6 documents

---

### ✅ Step 8: Test Full Application

- [ ] Start Fraud Backend → `http://localhost:8000`
- [ ] Start AML Backend → `http://localhost:8001`
- [ ] Start Frontend → `http://localhost:3000`
- [ ] Test: Transaction Simulator (run a "Multiple Red Flags" scenario)
- [ ] Test: Entity Management (search for an entity)
- [ ] Test: Entity Resolution (5-step workflow)
- [ ] Test: Agentic Investigation (launch one investigation)
- [ ] Test: ThreatSight Copilot (ask a question)
- [ ] Test: Risk Model Management (modify a risk factor)

---

## 💾 PHASE 2 — BEFORE TERMINATING (SAVE EVERYTHING)

> ⚠️ Do this BEFORE pausing/terminating the cluster

### 🗃️ Save Credentials Securely (Offline)

- [ ] Save `MONGODB_URI` (with username + password) in a secure place (notepad offline / password manager)
- [ ] Save `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
- [ ] Save `VOYAGE_API_KEY`
- [ ] Save all 3 `.env` files in a **secure offline location** (DO NOT push to GitHub)

### 📸 Take Atlas Snapshot / Backup

- [ ] In Atlas UI → Your Cluster → **...** (three dots) → **Take Snapshot Now**
  - Snapshot name: `pre-presentation-backup`
  - ✅ Wait for snapshot to complete
- [ ] Note the snapshot ID/date: `__________________`

### 🗂️ Note All Search Index Names (for re-creation if needed)

- [ ] `transaction_vector_index` — on `transactions`
- [ ] `entity_vector_search_index` — on `entities`
- [ ] `entity_resolution_search` — on `entities`
- [ ] `entity_text_search_index` — on `entities`

### ⏸️ Pause / Terminate the Cluster

> **Pause** = cluster sleeps, data preserved, costs stop (~$0/day)
> **Terminate** = cluster deleted (restore from snapshot needed)

**Recommended: PAUSE (not terminate)**

- [ ] Atlas UI → Cluster → **...** → **Pause Cluster**
  - ✅ Paused clusters keep all data + indexes intact
  - ✅ Resume in seconds before presentation day
  - ⚠️ Paused clusters auto-resume after 30 days (Atlas limit)

If you must **Terminate**:
- [ ] Atlas UI → Cluster → **...** → **Terminate**
  - ⚠️ You will need to restore from snapshot + recreate indexes

---

## 🔄 PHASE 3 — RECOVERY (DAY BEFORE PRESENTATION)

### Option A — If Cluster Was PAUSED (Easy ✅)

- [ ] Log in to [cloud.mongodb.com](https://cloud.mongodb.com)
- [ ] Find your cluster → Click **Resume**
- [ ] Wait ~2-3 minutes for cluster to come back online
- [ ] Verify connection string still works (same URI)
- [ ] All data + indexes are already there ✅
- [ ] Go to **Step: Verify Recovery** below

---

### Option B — If Cluster Was TERMINATED (Restore from Snapshot)

- [ ] Log in to Atlas → Create a **new M10 cluster** (same region)
- [ ] Go to **Backup** → **Snapshots** → Find `pre-presentation-backup`
- [ ] Click **Restore** → Select the new cluster
- [ ] Wait for restore to complete (~10-20 min)
- [ ] After restore, update `MONGODB_URI` if cluster name changed
- [ ] **Re-create all Search Indexes** (data will be there but indexes may need rebuilding):
  - [ ] `transaction_vector_index` on `transactions`
  - [ ] `entity_vector_search_index` on `entities`
  - [ ] `entity_resolution_search` on `entities`
  - [ ] `entity_text_search_index` on `entities`
- [ ] Wait for all indexes to build (status: **Active**)

---

### ✅ Verify Recovery (Both Options)

- [ ] Start Fraud Backend → confirm `http://localhost:8000/health` responds
- [ ] Start AML Backend → confirm `http://localhost:8001/health` responds
- [ ] Start Frontend → `http://localhost:3000` loads
- [ ] Verify in Atlas: document counts match expected values:
  - `customers` → ~50 | `transactions` → ~26,000 | `entities` → ~504
- [ ] Test Transaction Simulator → run one scenario
- [ ] Test Entity search → find an entity
- [ ] Test Copilot → ask "what entities are high risk?"
- [ ] Test Investigation → launch one investigation

---

## 🎤 PRESENTATION DAY CHECKLIST

- [ ] All 3 backends running (ports 8000, 8001, 3000)
- [ ] Network access in Atlas allows your presentation device IP
- [ ] Browser open at `http://localhost:3000`
- [ ] Role selected: **Risk Analyst** (for most features)
- [ ] Test one full flow 30 mins before presentation starts
- [ ] AWS Bedrock model access is active (not expired)
- [ ] Backup: have Atlas UI open in another tab in case of live issues

---

## 📋 CREDENTIALS REFERENCE CARD (Fill & Save Offline)

| Service | Key | Value |
|---|---|---|
| MongoDB Atlas | Cluster URI | `mongodb+srv://...` |
| MongoDB Atlas | DB Username | |
| MongoDB Atlas | DB Password | |
| AWS | Access Key ID | `AKIA...` |
| AWS | Secret Access Key | |
| AWS | Region | `us-east-1` |
| Voyage AI | API Key | |

> ⚠️ Never commit this file or your `.env` files to GitHub!
