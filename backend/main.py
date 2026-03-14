from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import uuid
import random
import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import (
    users_collection,
    behavior_collection,
    risk_collection,
    admin_notifications
)
from email_service import send_email

# ================= TIMEZONE =================
IST = timezone(timedelta(hours=5, minutes=30))

# ================= APP =================

app = FastAPI(title="AI-Based Zero Trust Security System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow frontend requests
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================= ROOT =================

@app.get("/")
def root():
    return {"status": "Zero Trust Backend Running"}

# ================= MODELS =================

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    mobile: str

class LoginRequest(BaseModel):
    username: str
    password: str

class BehaviorRequest(BaseModel):
    user_id: str
    location: str
    device: str
    access_speed: float

class VerifyRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

# ================= REGISTER =================

@app.post("/register")
async def register(data: RegisterRequest):
    if users_collection.find_one({"username": data.username}):
        raise HTTPException(400, "User already exists")

    users_collection.insert_one({
        "username": data.username,
        "password": pwd.hash(data.password),
        "email": data.email,
        "mobile": data.mobile,
        "role": "user",
        "status": "active",
        "created_at": datetime.now(IST)
    })

    return {"message": "Registration successful"}

# ================= LOGIN =================

@app.post("/login")
async def login(data: LoginRequest):

    user = users_collection.find_one({"username": data.username})

    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not pwd.verify(data.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")

    if user["status"] == "blocked":
        raise HTTPException(403, "Account blocked")

    return {
        "user_id": str(user["_id"]),
        "role": user["role"],
        "message": "Login successful"
    }

# ================= LOG BEHAVIOR =================

@app.post("/log-behavior")
async def log_behavior(data: BehaviorRequest):
    behavior_collection.insert_one({
        **data.dict(),
        "timestamp": datetime.now(IST)
    })
    return {"message": "Behavior logged"}

# ================= ANALYZE RISK =================

@app.post("/analyze-risk/{user_id}")
async def analyze_risk(user_id: str):
    logs = list(behavior_collection.find({"user_id": user_id}))

    if len(logs) < 3:
        return {"risk_level": "Low", "risk_score": 20, "action": "Allowed"}

    speeds = np.array([[l["access_speed"]] for l in logs])
    anomalies = list(
        IsolationForest(contamination=0.3, random_state=42)
        .fit_predict(speeds)
    ).count(-1)

    texts = [f'{l["location"]} {l["device"]}' for l in logs]
    tfidf = TfidfVectorizer().fit_transform(texts)
    similarity = cosine_similarity(tfidf[-1:], tfidf[:-1]).mean()

    if anomalies >= 1 or similarity < 0.7:
        user = users_collection.find_one({"_id": ObjectId(user_id)})

        risk_collection.insert_one({
            "user_id": user_id,
            "username": user["username"],
            "risk_score": random.randint(40, 95),
            "risk_level": "High",
            "timestamp": datetime.now(IST)
        })

        if user["status"] != "blocked":
            token = str(uuid.uuid4())

            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "status": "blocked",
                    "verify_token": token,
                    "blocked_at": datetime.now(IST)
                }}
            )

            admin_notifications.insert_one({
                "user_id": user_id,
                "username": user["username"],
                "risk_level": "High",
                "message": "User blocked – verification required",
                "timestamp": datetime.now(IST)
            })

            send_email(
                user["email"],
                "Zero Trust Alert – Account Blocked",
                f"Verification Token:\n{token}"
            )

        return {"risk_level": "High", "risk_score": 85, "action": "Blocked"}

    return {"risk_level": "Medium", "risk_score": 50, "action": "Restricted"}

# ================= VERIFY USER =================

@app.post("/verify-user")
async def verify_user(data: VerifyRequest):
    user = users_collection.find_one({"verify_token": data.token})

    if not user:
        raise HTTPException(400, "Invalid token")

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"status": "active"},
         "$unset": {"verify_token": "", "blocked_at": ""}}
    )

    admin_notifications.delete_many({"username": user["username"]})
    behavior_collection.delete_many({"user_id": str(user["_id"])})
    risk_collection.delete_many({"user_id": str(user["_id"])})

    return {"message": "User verified"}

# ================= ADMIN UNBLOCK =================

@app.post("/admin/unblock/{username}")
async def admin_unblock(username: str):
    user = users_collection.find_one({"username": username})

    if not user:
        raise HTTPException(404, "User not found")

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"status": "active"},
         "$unset": {"verify_token": "", "blocked_at": ""}}
    )

    admin_notifications.delete_many({"username": username})
    behavior_collection.delete_many({"user_id": str(user["_id"])})
    risk_collection.delete_many({"user_id": str(user["_id"])})

    return {"message": "User unblocked"}

# ================= FORGOT PASSWORD =================

@app.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    user = users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(404, "Email not found")

    otp = str(random.randint(100000, 999999))

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"reset_otp": otp}}
    )

    # send_email(
    #     data.email,
    #     "Password Reset OTP",
    #     f"Your OTP is: {otp}"
    # )
    print(f"OTP for {data.email}: {otp}")
    return {"message": "OTP sent"}

# ================= RESET PASSWORD =================

@app.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    user = users_collection.find_one({
        "email": data.email,
        "reset_otp": data.otp
    })

    if not user:
        raise HTTPException(400, "Invalid OTP")

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": pwd.hash(data.new_password)},
         "$unset": {"reset_otp": ""}}
    )

    return {"message": "Password reset successful"}

# ================= ADMIN ALERTS =================

@app.get("/admin-notifications")
async def get_admin_notifications():
    return [
        {**a, "_id": str(a["_id"])}
        for a in admin_notifications.find().sort("timestamp", -1)
    ]

# ================= RISK REPORTS =================

@app.get("/risk-reports")
async def risk_reports():
    return [
        {**r, "_id": str(r["_id"])}
        for r in risk_collection.find().sort("timestamp", 1)
    ]
# ================= SERVE FRONTEND =================

frontend_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")

if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        index_file = os.path.join(frontend_path, "index.html")
        return FileResponse(index_file)
@app.on_event("startup")
def create_db_test():
    users_collection.insert_one({"test": "database connection working"})
    print("✅ Test document inserted")