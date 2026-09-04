import os
from pymongo import MongoClient
import certifi

MONGODB_URI = 'mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY@aml-demo-cluster.klrgot.mongodb.net/sentinelai?retryWrites=true&w=majority&appName=aml-demo-cluster'

try:
    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    db = client['sentinelai']

    # Find Mohadev Gaming Consultancy LLP
    doc = db['sentinelaiEntities'].find_one({'fullName': {'$regex': 'Mohadev Gaming'}})
    if doc:
        print("Found:", doc['fullName'], doc['entityId'])
        ent_id = doc['entityId']
        txns = db['transactionsv2'].count_documents({'$or': [{'fromEntityId': ent_id}, {'toEntityId': ent_id}]})
        print("Txns fromEntityId/toEntityId:", txns)
        txns_old = db['transactionsv2'].count_documents({'$or': [{'entityId': ent_id}, {'counterpartyEntityId': ent_id}]})
        print("Txns entityId/counterpartyEntityId:", txns_old)
    else:
        print("Not found")

except Exception as e:
    print('Error:', e)
