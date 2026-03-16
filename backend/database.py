from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://ZeroTrustadmin:ZeroTrust123@cluster0.mkqmvyb.mongodb.net/?appName=Cluster0")

client = MongoClient(MONGO_URL)

db = client["zero_trust_db"]

users_collection = db["users"]
behavior_collection = db["behavior_logs"]
risk_collection = db["risk_reports"]
admin_notifications = db["admin_notifications"]