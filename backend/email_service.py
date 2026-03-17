import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID")
TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID")
PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("EMAILJS_PRIVATE_KEY")

def send_email(to_email, subject, message, otp=None):
    """
    Sends an email using EmailJS REST API.
    """
    if not all([SERVICE_ID, TEMPLATE_ID, PUBLIC_KEY, PRIVATE_KEY]):
        print("❌ EMAILJS credentials missing in .env")
        return

    print(f"📧 Attempting to send email to: {to_email} via EmailJS")

    url = "https://api.emailjs.com/api/v1.0/email/send"
    
    data = {
        "service_id": SERVICE_ID,
        "template_id": TEMPLATE_ID,
        "user_id": PUBLIC_KEY,
        "accessToken": PRIVATE_KEY,
        "template_params": {
            "to_email": to_email,
            "subject": subject,
            "message": message,
            "otp": otp if otp else ""
        }
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ Email Sent Successfully via EmailJS!")
        else:
            print(f"❌ EmailJS API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Request Error: {e}")