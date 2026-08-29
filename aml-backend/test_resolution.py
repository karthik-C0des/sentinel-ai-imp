import sys
import os
import json
from fastapi.testclient import TestClient

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)

def run_tests():
    print("Testing Enhanced Entity Resolution Section")
    print("========================================")
    
    # 1. Test Demo Scenarios
    print("\n1. Testing GET /api/v1/resolution/demo-scenarios-enhanced")
    response = client.get("/api/v1/resolution/demo-scenarios-enhanced")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        scenarios = data.get("scenarios", [])
        print(f"Success! Retrieved {len(scenarios)} scenarios.")
        if scenarios:
            print(f"First scenario: {scenarios[0]['name']}")
    else:
        print(f"Failed: {response.text}")

    # 2. Test Comprehensive Search
    print("\n2. Testing POST /api/v1/resolution/comprehensive-search")
    search_payload = {
        "entity": {
            "fullName": "Lisa Anderson",
            "address": "269 Brian Trail, Freybury, 89323, Brazil",
            "entityType": "individual"
        },
        "searchConfig": {
            "maxResults": 2,
            "confidenceThreshold": 0.3,
            "atlasWeight": 1,
            "vectorWeight": 1
        }
    }
    
    response = client.post("/api/v1/resolution/comprehensive-search", json=search_payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Results:")
        print(f"- Atlas Results: {len(data.get('atlasResults', []))}")
        print(f"- Vector Results: {len(data.get('vectorResults', []))}")
        print(f"- Hybrid Results: {len(data.get('hybridResults', []))}")
    else:
        print(f"Failed: {response.text}")

    # 3. Test Analyze Intelligence
    print("\n3. Testing POST /api/v1/resolution/analyze-intelligence")
    intelligence_payload = {
        "searchResults": {
            "atlasResults": [{"entityId": "1", "matchScore": 0.9, "riskAssessment": {"overall": {"score": 80}}}],
            "vectorResults": [{"entityId": "1", "matchScore": 0.88, "riskAssessment": {"overall": {"score": 80}}}],
            "correlationAnalysis": {
                "correlationPercentage": 90,
                "confidenceScore": 0.89,
                "intersectionCount": 1
            }
        }
    }
    response = client.post("/api/v1/resolution/analyze-intelligence", json=intelligence_payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Patterns found:")
        for pattern in data.get("patterns", []):
            print(f"- {pattern['type']}: {pattern['description']}")
    else:
        print(f"Failed: {response.text}")

    # 4. Test Network Analysis
    print("\n4. Testing POST /api/v1/resolution/network-analysis")
    network_payload = {
        "centerEntity": {
            "fullName": "Lisa Anderson",
            "entityType": "individual"
        },
        "relatedEntities": [
            {"entityId": "65b2d71b9c9f2a8e4b7b7a1d"}
        ],
        "analysisConfig": {
            "maxDepth": 1,
            "minConfidence": 0.5
        }
    }
    response = client.post("/api/v1/resolution/network-analysis", json=network_payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Network Statistics:")
        print(json.dumps(data.get("networkStatistics", {}), indent=2))
    else:
        print(f"Failed: {response.text}")

    # 5. Test Classify Entity
    print("\n5. Testing POST /api/v1/resolution/classify-entity")
    classify_payload = {
        "entity": {
            "fullName": "Lisa Anderson"
        },
        "searchResults": {
            "atlasResults": [{"entityId": "1", "matchScore": 0.95}],
            "vectorResults": []
        },
        "intelligence": {
            "riskIndicators": []
        }
    }
    response = client.post("/api/v1/resolution/classify-entity", json=classify_payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Classification: {data.get('classification')}")
        print(f"Reasoning: {data.get('reasoning')}")
    else:
        print(f"Failed: {response.text}")

if __name__ == "__main__":
    run_tests()
