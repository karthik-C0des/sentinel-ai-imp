import requests

base_url = 'http://localhost:8001/api/v1/resolution'
response = requests.get(f'{base_url}/demo-scenarios-enhanced')
marco = next(s for s in response.json()['scenarios'] if 'Marco' in s['name'])
search_payload = {
    'entity': marco['entityData'],
    'searchConfig': {
        'maxResults': 10,
        'confidenceThreshold': 0.3,
        'atlasWeight': 1.0,
        'vectorWeight': 1.0
    }
}
res = requests.post(f'{base_url}/comprehensive-search', json=search_payload).json()
print(f"Atlas: {len(res['atlasResults'])}, Vector: {len(res['vectorResults'])}, Hybrid: {len(res.get('hybridResults', []))}")
