import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from repositories.impl.transaction_repository import TransactionRepository

async def run():
    client = AsyncIOMotorClient('mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY@aml-demo-cluster.klrgot.mongodb.net/threatsight360?retryWrites=true&w=majority&appName=aml-demo-cluster')
    db = client.threatsight360
    repo = TransactionRepository(db.transactionsv2)
    try:
        result = await repo.build_transaction_network('ENT-0394', max_depth=1)
        print('Nodes:', len(result.nodes))
        print('Edges:', len(result.edges))
    except Exception as e:
        print('Error:', str(e))

asyncio.run(run())
