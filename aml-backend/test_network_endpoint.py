import asyncio, httpx, json
async def main():
    async with httpx.AsyncClient() as client:
        # Give backend time to start up
        await asyncio.sleep(5)
        try:
            r = await client.get('http://localhost:8001/network/ENT-0435?max_depth=2', timeout=10.0)
            data = r.json()
            print(f"Nodes: {len(data.get('nodes', []))}, Edges: {len(data.get('edges', []))}")
        except Exception as e:
            print(f"Error: {e}")
asyncio.run(main())
