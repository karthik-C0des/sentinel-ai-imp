import asyncio
import httpx

async def test_unified_search():
    url = "http://localhost:8001/entities/search/unified"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"limit": 20, "page": 1})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", {}).get("results", [])
            print(f"Results count: {len(results)}")
            for r in results[:5]:
                print(f" - {r.get('name', {}).get('full')}")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_unified_search())
