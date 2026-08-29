import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient('mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY@aml-demo-cluster.klrgot.mongodb.net/threatsight360?retryWrites=true&w=majority&appName=aml-demo-cluster')
    db = client.threatsight360
    # Find a transaction with a specific ID to see if it's duplicated
    docs = await db.transactionsv2.find({'transactionId': 'TXNV2-000001'}).to_list(10)
    print('Count for TXNV2-000001:', len(docs))
    for doc in docs:
        print(doc.get('entityId'), doc.get('direction'), doc.get('counterpartyEntityId'))

asyncio.run(run())
