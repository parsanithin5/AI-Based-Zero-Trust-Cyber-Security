# from pymongo import MongoClient

# MONGO_URL = "mongodb+srv://zerotrustadmin:ZeroTrust123@cluster0.ebhkf16.mongodb.net/?appName=Cluster0"

# client = MongoClient(MONGO_URL)

# db = client["zero_trust_db"]

# users_collection = db["users"]
# behavior_collection = db["behavior_logs"]
# risk_collection = db["risk_reports"]
# admin_notifications = db["admin_notifications"]
# print("✅ Connected to MongoDB:", client)

# from pymongo import MongoClient
# import certifi
# import os

# MONGO_URL = os.getenv("MONGO_URL")

# client = MongoClient(
#     MONGO_URL,
#     tls=True,
#     tlsCAFile=certifi.where()
# )

# db = client["sample_mflix"]

# users_collection = db["users"]
# behavior_collection = db["behavior_logs"]
# risk_collection = db["risk_reports"]
# admin_notifications = db["admin_notifications"]from pymongo import MongoClient
from pymongo import MongoClient
MONGO_URL = "mongodb+srv://ZeroTrustadmin:ZeroTrust123@cluster0.mkqmvyb.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URL)

db = client["zero_trust_db"]

users_collection = db["users"]
behavior_collection = db["behavior_logs"]
risk_collection = db["risk_reports"]
admin_notifications = db["admin_notifications"]