from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import uuid
import random
import numpy as np
from dotenv import load_dotenv
import logging
import traceback
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

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

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("zero_trust_api")

# ================= SECURITY CONFIG =================
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-production-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
PROD_MODE = os.getenv("RENDER", "false").lower() == "true"

# ================= TIMEZONE =================
IST = timezone(timedelta(hours=5, minutes=30))

# ================= APP =================
app = FastAPI(
    title="AI-Based Zero Trust Security System",
    docs_url="/docs" if not PROD_MODE else None,
    redoc_url="/redoc" if not PROD_MODE else None
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user

# ================= STARTUP =================
@app.on_event("startup")
async def startup_db_client():
    try:
        users_collection.create_index("username", unique=True)
        users_collection.create_index("email", unique=True)
        logger.info("Database unique indexes verified/created.")
    except Exception as e:
        logger.warning(f"Could not enforce unique indexes on startup (duplicates may already exist manually clean DB): {e}")

from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"🚨 GLOBAL ERROR: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
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
            raise HTTPException(400, "Username already exists")

        if users_collection.find_one({"email": data.email}):
            raise HTTPException(400, "Email already in use")

        # Generate a 6-digit OTP for registration verification
        otp = str(random.randint(100000, 999999))
        logger.info(f"Generated OTP for user {data.username}")

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

        logger.info(f"Attempting to insert user {data.username} into database")
        users_collection.insert_one(user_data)
        logger.info(f"Successfully inserted user {data.username}")

        # Send OTP via EmailJS
        logger.info(f"Attempting to send email to {data.email}")
        send_email(
            data.email,
            "Verify Your Account",
            "Welcome to the Zero Trust Security System! Please use the following One-Time Password (OTP) to complete your verification process.",
            otp=otp
        )
        logger.info(f"send_email call completed")

        return {"message": "OTP sent to your email. Please verify."}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ REGISTRATION ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Registration failed: {str(e)}")

# ================= LOGIN =================

@app.post("/login")
async def login(data: LoginRequest):
    try:
        logger.info(f"Login attempt for username: {data.username}")
        user = users_collection.find_one({"username": data.username})

        if not user:
            logger.warning(f"User '{data.username}' not found")
            raise HTTPException(401, "Invalid credentials")

        if not pwd.verify(data.password, user["password"]):
            logger.warning(f"Password verification failed for '{data.username}'")
            raise HTTPException(401, "Invalid credentials")

        if user.get("status") == "blocked":
            logger.warning(f"User '{data.username}' is blocked")
            raise HTTPException(403, "Account blocked")

        access_token = create_access_token(data={"sub": user["username"]})
        
        logger.info(f"Login successful for user '{data.username}'")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user["_id"]),
            "role": user["role"],
            "message": "Login successful"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ LOGIN ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Login failed: {str(e)}")

# ================= LOG BEHAVIOR =================

@app.post("/log-behavior")
async def log_behavior(data: BehaviorRequest, current_user: dict = Depends(get_current_user)):
    behavior_collection.insert_one({
        **data.dict(),
        "timestamp": datetime.now(IST)
    })
    return {"message": "Behavior logged"}

# ================= ANALYZE RISK =================

@app.post("/analyze-risk/{user_id}")
async def analyze_risk(user_id: str, current_user: dict = Depends(get_current_user)):
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

    access_token = create_access_token(data={"sub": user["username"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user["_id"]),
        "role": user["role"],
        "message": "User verified"
    }

# ================= ADMIN UNBLOCK =================

@app.post("/admin/unblock/{username}")
async def admin_unblock(username: str, current_user: dict = Depends(get_current_user)):
    # Verify admin role
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
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

# ================= FORGOT / RESET PASSWORD =================

@app.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    user = users_collection.find_one({"email": data.email})
    if not user:
        logger.warning(f"Forgot password attempt for non-existent email: {data.email}")
        raise HTTPException(404, "User not found")

    otp = str(random.randint(100000, 999999))
    expiry = datetime.now(IST) + timedelta(minutes=10)

    users_collection.update_one(
        {"email": data.email},
        {"$set": {"otp": otp, "otp_expiry": expiry}}
    )

    logger.info(f"Sending password reset OTP to {data.email}")
    send_email(
        data.email,
        "Password Reset OTP",
        "You requested a password reset. Please use the following One-Time Password (OTP) to reset your password. This OTP will expire in 10 minutes.",
        otp=otp
    )

    return {"message": "OTP sent to your email"}

@app.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    user = users_collection.find_one({
        "email": data.email,
        "otp": data.otp
    })

    if not user:
        logger.warning(f"Invalid OTP attempt for {data.email}")
        raise HTTPException(400, "Invalid OTP or email")

    if datetime.now(IST) > user.get("otp_expiry", datetime.min.replace(tzinfo=IST)):
        logger.warning(f"Expired OTP attempt for {data.email}")
        raise HTTPException(400, "OTP has expired")

    users_collection.update_one(
        {"email": data.email},
        {"$set": {"password": pwd.hash(data.new_password)},
         "$unset": {"otp": "", "otp_expiry": ""}}
    )

    logger.info(f"Password reset successful for {data.email}")
# ================= ADMIN DASHBOARD =================

@app.get("/admin/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return list(admin_notifications.find({}, {"_id": 0}).sort("timestamp", -1))

@app.get("/admin/risk-reports")
async def get_risk_reports(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return list(risk_collection.find({}, {"_id": 0}).sort("timestamp", -1))

@app.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    users = list(users_collection.find({}, {"password": 0, "verify_token": 0}))
    for u in users:
        u["_id"] = str(u["_id"])
    return users

# ================= DB CHECK =================

@app.get("/db-check")
async def db_check():
    try:
        from database import client, MONGO_URL
        # Mask the password in MONGO_URL for security
        masked_url = "URL Hidden"
        if MONGO_URL:
            host_part = MONGO_URL.split("@")[-1] if "@" in MONGO_URL else "Unknown"
            masked_url = f"mongodb+srv://***:***@{host_part}"
            
        client.admin.command('ping')
        count = users_collection.count_documents({})
        return {
            "status": "connected",
            "database": "Atlas",
            "host": client.address,
            "url_detected": masked_url,
            "user_count": count,
            "message": "Database is reachable and responding."
        }
    except Exception as e:
        from database import MONGO_URL
        host_part = MONGO_URL.split("@")[-1] if MONGO_URL and "@" in MONGO_URL else "Unknown"
        return {
            "status": "error",
            "url_detected": f"mongodb+srv://***:***@{host_part}",
            "message": str(e)
        }

# ================= SERVE FRONTEND =================

frontend_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")

if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        index_file = os.path.join(frontend_path, "index.html")
        return FileResponse(index_file)

# No startup events currently needed