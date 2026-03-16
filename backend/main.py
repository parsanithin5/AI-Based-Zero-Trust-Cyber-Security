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
from dotenv import load_dotenv

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

# ================= LOAD ENV =================
load_dotenv()

# ================= TIMEZONE =================
IST = timezone(timedelta(hours=5, minutes=30))

# ================= APP =================

app = FastAPI(title="AI-Based Zero Trust Security System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Frontend is served at / by the catch-all route at the bottom

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
    try:
        if users_collection.find_one({"username": data.username}):
            raise HTTPException(400, "User already exists")

        # Generate a 6-digit OTP for registration verification
        otp = str(random.randint(100000, 999999))
        print(f"DEBUG: Generated OTP {otp} for user {data.username}")

        user_data = {
            "username": data.username,
            "password": pwd.hash(data.password),
            "email": data.email,
            "mobile": data.mobile,
            "role": "user",
            "status": "pending",
            "verify_token": otp,
            "created_at": datetime.now(IST)
        }

        print(f"DEBUG: Attempting to insert user {data.username} into database")
        users_collection.insert_one(user_data)
        print(f"DEBUG: Successfully inserted user {data.username}")

        # Send OTP via MailerSend
        print(f"DEBUG: Attempting to send email to {data.email}")
        send_email(
            data.email,
            "Zero Trust Security - Registration OTP",
            f"Thank you for registering. Your verification OTP is: {otp}"
        )
        print(f"DEBUG: send_email call completed")

        return {"message": "OTP sent to your email. Please verify."}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ REGISTRATION ERROR: {str(e)}")
        # Log the full error to Render console
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Registration failed: {str(e)}")

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
        
        # Ensure consistent high risk score
        risk_score = random.randint(80, 95)

        risk_collection.insert_one({
            "user_id": user_id,
            "username": user["username"],
            "risk_score": risk_score,
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

        return {"risk_level": "High", "risk_score": risk_score, "action": "Blocked"}

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

    expiry_time = datetime.now(IST) + timedelta(minutes=5)

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "reset_otp": otp,
            "otp_expiry": expiry_time
        }}
    )

    send_email(
        data.email,
        "Password Reset OTP",
        f"Your OTP is: {otp}"
    )

    return {"message": "OTP sent (valid for 5 minutes)"}

# ================= RESET PASSWORD =================

@app.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):

    user = users_collection.find_one({
        "email": data.email,
        "reset_otp": data.otp
    })

    if not user:
        raise HTTPException(400, "Invalid OTP")

    if datetime.now(IST) > user.get("otp_expiry"):
        raise HTTPException(400, "OTP expired")

    users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": pwd.hash(data.new_password)},
            "$unset": {
                "reset_otp": "",
                "otp_expiry": ""
            }
        }
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

# No startup events currently needed