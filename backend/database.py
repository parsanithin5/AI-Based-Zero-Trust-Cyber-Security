# from pymongo import MongoClient

# client = MongoClient("mongodb://localhost:27017")
# db = client["zero_trust_db"]

# users_collection = db["users"]
# behavior_collection = db["behavior_logs"]
# risk_collection = db["risk_reports"]
# admin_notifications = db["admin_notifications"]
from pymongo import MongoClient

MONGO_URL = "mongodb+srv://zerotrustadmin:ZeroTrust123@cluster0.ebhkf16.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URL)

db = client["zero_trust_db"]

users_collection = db["users"]
behavior_collection = db["behavior_logs"]
risk_collection = db["risk_reports"]
admin_notifications = db["admin_notifications"]