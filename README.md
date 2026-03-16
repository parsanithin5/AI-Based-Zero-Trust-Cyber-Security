# 🛡️ AI-Based Zero Trust Cyber Security System

An intelligent cybersecurity system that uses **Machine Learning** to detect anomalous behavior and enforce Zero Trust access policies in real time.

## 🚀 Live Demo
[https://ai-based-zero-trust-cyber-security.onrender.com](https://ai-based-zero-trust-cyber-security.onrender.com)

---

## 🧠 How It Works

1. Users log in and their access behavior (location, device, speed) is logged
2. An **Isolation Forest** ML model detects speed anomalies
3. **TF-IDF + Cosine Similarity** checks if device/location patterns deviate
4. If risk is **High** → account is blocked automatically + verification email is sent
5. Admin can view alerts and unblock users from the dashboard

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | MongoDB Atlas |
| ML | scikit-learn (Isolation Forest, TF-IDF) |
| Email | MailerSend API |
| Frontend | React 18 + Vite |
| Charts | Recharts |
| Hosting | Render |

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py           # All API routes
│   ├── database.py       # MongoDB connection
│   ├── email_service.py  # MailerSend integration
│   ├── models.py         # Pydantic models
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx       # Single-page React app
        └── index.css     # Global styles
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/register` | POST | Register a new user |
| `/login` | POST | Authenticate user/admin |
| `/log-behavior` | POST | Log access behavior |
| `/analyze-risk/{user_id}` | POST | Run AI risk analysis |
| `/verify-user` | POST | Unblock via email token |
| `/forgot-password` | POST | Send OTP to email |
| `/reset-password` | POST | Reset password with OTP |
| `/admin/unblock/{username}` | POST | Admin unblock user |
| `/admin-notifications` | GET | View security alerts |
| `/risk-reports` | GET | View risk history |

---

## ⚙️ Local Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables (Render / .env)
```
MAILERSEND_API_KEY=your_mailersend_token
MONGO_URL=your_mongodb_connection_string
```

---

## 👤 Roles

- **User** — logs behavior and triggers risk analysis
- **Admin** — views alerts, risk charts, and unblocks users
