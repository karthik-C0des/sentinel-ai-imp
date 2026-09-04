import os
from pymongo import MongoClient
import certifi

uri = "mongodb+srv://repallekarthik11_db_user:kBzF1zL5nr1wVdLY@aml-demo-cluster.klrgot.mongodb.net/sentinelai?retryWrites=true&w=majority&appName=aml-demo-cluster"
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client["sentinelai"]
collection = db["transactions"]

latest_tx = collection.find_one({}, sort=[("createdAt", -1)])
print("Latest transaction createdAt:", latest_tx.get("createdAt") if latest_tx else "None")

count = collection.count_documents({})
print("Total transactions:", count)
