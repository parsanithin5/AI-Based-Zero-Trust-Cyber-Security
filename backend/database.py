from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)

db = client["zero_trust_db"]

users_collection = db["users"]
behavior_collection = db["behavior_logs"]
risk_collection = db["risk_reports"]
admin_notifications = db["admin_notifications"]