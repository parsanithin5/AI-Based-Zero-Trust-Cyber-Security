import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API_KEY = os.getenv("MAILERSEND_API_KEY")
SENDER_EMAIL = os.getenv("MAILERSEND_SENDER")

def send_email(to_email, subject, body):
    """
    Sends an email using MailerSend HTTP API directly (avoiding SDK version issues).
    """
    if not API_KEY:
        print("❌ MAILERSEND_API_KEY not found in environment variables")
        return
    
    if not SENDER_EMAIL:
        print("❌ MAILERSEND_SENDER not found in environment variables")
        return

    print(f"📧 Attempting to send email to: {to_email}")

    url = "https://api.mailersend.com/v1/email"
    
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "from": {
            "email": SENDER_EMAIL,
            "name": "Zero Trust Security"
        },
        "to": [
            {
                "email": to_email,
                "name": "Security User"
            }
        ],
        "subject": subject,
        "text": body,
        "html": f"<div style='font-family: Arial; padding: 20px; border: 1px solid #ddd; border-radius: 8px;'><h2>{subject}</h2><p>{body}</p></div>"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 202:
            print(f"✅ Email Sent Successfully! Status Code: {response.status_code}")
        else:
            print(f"❌ MailerSend API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Request Error: {e}")