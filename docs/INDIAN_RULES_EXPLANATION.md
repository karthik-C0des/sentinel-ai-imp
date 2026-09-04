# Indian AML & Cybercrime Rules in Sentinel-AI

This document explains the specific Indian rules, policies, and regulations implemented in the Sentinel-AI project, how they are utilized, and the rationale behind their inclusion. It also outlines potential future rules that can be added to further enhance compliance with Indian regulations.

---

## Part 1: Currently Implemented Rules

### 1. Rule 114B of the Income Tax Rules (PAN Structuring)
#### What it is
Under Rule 114B of the Indian Income Tax Rules, any cash deposit or transaction exceeding ₹50,000 requires the customer to provide their Permanent Account Number (PAN). 
#### How it is used
The synthetic data generation script (`generate_indian_demo_data.py`) creates specific transactions where amounts are deliberately kept between ₹48,000 and ₹49,950. These transactions are flagged as **Rule 114B PAN Structuring**.
#### Why we use it
Fraudsters and money launderers often use "smurfing" or "structuring"—breaking down large transactions into smaller ones that fall just below the regulatory threshold—to avoid detection and PAN reporting. Simulating this helps the AI agent learn to detect structuring behavior designed to evade Indian tax monitoring systems.

### 2. PMLA Section 12 CTR (Cash Transaction Report)
#### What it is
The Prevention of Money Laundering Act (PMLA) Section 12 requires financial institutions to maintain records of and report all cash transactions exceeding ₹10 Lakhs (or its equivalent in foreign currency) in a single month.
#### How it is used
The system synthesizes branch cash deposit transactions with values intentionally set between ₹10.5 Lakhs and ₹32 Lakhs. These are explicitly flagged as **PMLA CTR Large Cash Inflow** patterns.
#### Why we use it
Cash intensive businesses and illicit activities often rely on large, unexplained cash injections. By embedding these typologies, the platform's fraud detection engine is trained to trigger automated alerts for regulatory reporting to the Financial Intelligence Unit - India (FIU-IND).

### 3. 10% UBO (Ultimate Beneficial Ownership) RBI Rule
#### What it is
The Reserve Bank of India (RBI) mandates identifying the Ultimate Beneficial Owner (UBO) for corporate accounts. Recent amendments lower the threshold for determining a controlling ownership interest from 25% to 10% for companies and trusts.
#### How it is used
The `sentinelaiRelationships` multi-hop graph generation connects entities (individuals and organizations) through relationships like `owner_of`, `director_of`, and `subsidiary_of`. The system models these complex, multi-layered corporate structures to represent shell companies and holding-subsidiary networks.
#### Why we use it
Money laundering often hides behind complex webs of shell companies. Modeling these connections allows the system's graph analytics and Agentic Pipeline to trace back to the actual human beneficial owners, ensuring compliance with RBI's strict KYC/AML guidelines and identifying hidden risk networks.

### 4. UPI Mule Ring Fan-out (I4C 1930 Cyber Helpline Pattern)
#### What it is
The Indian Cybercrime Coordination Centre (I4C) under the Ministry of Home Affairs monitors cyber fraud. A common pattern reported via the 1930 helpline involves victims' funds being rapidly transferred through multiple UPI accounts (mule accounts) and then immediately liquidated at ATMs.
#### How it is used
The fraud patterns collection includes embeddings for **UPI Mule Ring Fan-out**, training the vector search engine to identify rapid inflows of UPI transfers followed by sudden liquidation.
#### Why we use it
India's high volume of UPI transactions has led to an explosion in instant digital fraud. Detecting these high-velocity "fan-out" and "fan-in" patterns is crucial for real-time freezing of fraudulent funds before they leave the banking system.

### 5. Digital Arrest Cyber Scam (IT Act Section 66D)
#### What it is
A rising cyber fraud typology in India where victims are coerced (often via fake police or CBI calls) into transferring large sums of money. This relates to offenses under Section 66D of the IT Act (cheating by personation using a computer resource).
#### How it is used
The system introduces anomalies such as uncharacteristic, high-value overnight RTGS transfers directed towards dummy corporate accounts, classified as **Digital Arrest Cyber Scams**.
#### Why we use it
Protecting vulnerable customers from real-time social engineering attacks requires behavioral analysis. Identifying deviations from a customer's normal transfer behavior (e.g., a sudden, massive overnight RTGS) allows the bank to intervene, hold the transaction, or alert the customer.

### 6. Shell Entity Hawala Layering
#### What it is
Hawala is an informal method of transferring money without moving physical currency, often used illegally to bypass standard banking channels. "Layering" involves moving funds through multiple shell entities to obscure the origin.
#### How it is used
The data generation simulates circular fund transfers moving through commercial Limited Liability Partnerships (LLPs) and private limited companies without clear economic substance or underlying trade.
#### Why we use it
Detecting Hawala and trade-based money laundering (TBML) is a high priority for Indian regulators (ED, DRI). By training the system on circular transactions and shell entity characteristics, it helps banks identify sophisticated, syndicated laundering operations.

---

## Part 2: Potential Rules for Future Addition

The following rules can be added to the synthetic data generation and vector search models to further enhance the system's compliance with RBI and Indian Government regulations:

### 7. RBI Liberalised Remittance Scheme (LRS) Breaches
#### What it is
Under the RBI's LRS, resident individuals are permitted to remit up to USD 250,000 (approx ₹2 Crore) per financial year for permissible current or capital account transactions.
#### How it can be used
We can generate structured outward wire/SWIFT transfers across multiple days or through multiple linked accounts that collectively exceed the ₹2 Crore limit.
#### Why we should use it
Evasion of LRS limits is a common method for illicit capital flight and tax evasion. Detecting this ensures compliance with FEMA (Foreign Exchange Management Act).

### 8. Dormant Account Activation (RBI KYC Master Direction)
#### What it is
According to RBI KYC Master Directions, sudden high-value transactions in an account that has been inactive or dormant for a long period (typically >12 months) must be flagged for Suspicious Transaction Reporting (STR).
#### How it can be used
We can create profiles for older customers featuring a massive, sudden influx of RTGS transfers followed by immediate cash or UPI withdrawals, simulating a hijacked or mule account.
#### Why we should use it
Fraudsters often purchase dormant accounts from individuals to use as temporary holding accounts for laundered money. Monitoring sudden activations is a fundamental AML control.

### 9. FCRA (Foreign Contribution Regulation Act) Anomalies
#### What it is
The Ministry of Home Affairs (MHA) strictly regulates foreign donations to Indian NGOs, trusts, and societies under the FCRA.
#### How it can be used
We can simulate foreign wire transfers arriving into a local corporate or trust account that lacks the proper FCRA registration indicators, or simulate sudden massive spikes in foreign donations from high-risk jurisdictions.
#### Why we should use it
FCRA compliance is highly scrutinized. Banks are penalized heavily for clearing foreign contributions to unregistered entities.

### 10. Trade-Based Money Laundering (TBML) via Phantom Shipments
#### What it is
Discrepancies in import/export data, such as over-invoicing or under-invoicing, are heavily monitored by the Directorate of Revenue Intelligence (DRI) and RBI.
#### How it can be used
We can generate massive outward remittances classified as "import of services/goods" by newly formed shell companies (LLPs) with no prior GST filing history or legitimate business profile.
#### Why we should use it
TBML is one of the most complex typologies to detect, requiring the correlation of transaction data with entity profiles and tax/customs histories. Adding this will showcase advanced graph analysis capabilities.
