import os
from pymongo import MongoClient
import certifi

MONGODB_URI = 'mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY@aml-demo-cluster.klrgot.mongodb.net/sentinelai?retryWrites=true&w=majority&appName=aml-demo-cluster'

try:
    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    db = client['sentinelai']

    print('Entity search for ENT-DEMO-006:')
    doc1 = db['sentinelaiEntities'].find_one({'entityId': 'ENT-DEMO-006'})
    doc2 = db['sentinelaiEntities'].find_one({'scenarioKey': 'ENT-DEMO-006'})
    print('By entityId:', doc1 is not None)
    print('By scenarioKey:', doc2 is not None)
    if doc1: print('entityId from doc1:', doc1.get('entityId'), 'scenarioKey:', doc1.get('scenarioKey'))
    if doc2: print('entityId from doc2:', doc2.get('entityId'), 'scenarioKey:', doc2.get('scenarioKey'))

    ent_id = doc1['entityId'] if doc1 else (doc2['entityId'] if doc2 else 'ENT-DEMO-006')

    print('Transactions for', ent_id)
    txns = db['transactionsv2'].count_documents({'$or': [{'fromEntityId': ent_id}, {'toEntityId': ent_id}]})
    print('Count:', txns)

    print('Relationships for', ent_id)
    rels = db['sentinelaiRelationships'].count_documents({'source.entityId': ent_id})
    print('Count:', rels)
except Exception as e:
    print('Error:', e)
