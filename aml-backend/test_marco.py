import requests
import json

base_url = "http://localhost:8001/api/v1/resolution"

print("1. Fetching demo scenarios...")
response = requests.get(f"{base_url}/demo-scenarios-enhanced")
if response.status_code != 200:
    print(f"Failed to fetch scenarios: {response.text}")
    exit(1)

scenarios = response.json().get('scenarios', [])
print(f"Found {len(scenarios)} scenarios.")

marco = None
for s in scenarios:
    if "Marco" in s.get("title", ""):
        marco = s
        break

if not marco:
    print("Marco Johnson scenario not found!")
    exit(1)

print(f"Selected scenario: {marco['title']}")

print("\n2. Sending comprehensive search request...")
search_payload = {
    "entityData": marco['entityData'],
    "searchConfig": {
        "maxResults": 10,
        "confidenceThreshold": 0.3,
        "atlasWeight": 1.0,
        "vectorWeight": 1.0
    }
}

response = requests.post(f"{base_url}/comprehensive-search", json=search_payload)
if response.status_code != 200:
    print(f"Comprehensive search failed: {response.text}")
    exit(1)

results = response.json()
atlas = results.get('atlasResults', [])
vector = results.get('vectorResults', [])
hybrid = results.get('hybridResults', [])

print(f"\nResults Summary:")
print(f"Atlas Search: {len(atlas)} results")
print(f"Vector Search: {len(vector)} results")
print(f"Hybrid Search: {len(hybrid)} results")

if len(atlas) == 0 or len(vector) == 0:
    print("\nWARNING: Atlas or Vector search returned 0 results for Marco Johnson!")
else:
    print("\nSUCCESS: All searches returned data.")
