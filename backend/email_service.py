import os
import requests
import logging
from dotenv import load_dotenv

# Load env variables if not already loaded
load_dotenv()
logger = logging.getLogger("email_service")

SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID")
TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID")
PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("EMAILJS_PRIVATE_KEY")

def send_email(to_email, subject, message, otp=None):
    """
    Sends an email using EmailJS REST API.
    """
    if not all([SERVICE_ID, TEMPLATE_ID, PUBLIC_KEY, PRIVATE_KEY]):
        logger.error("EmailJS credentials missing in .env")
        return

    logger.info(f"Attempting to send email to: {to_email}")

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
            logger.info("Email sent successfully via EmailJS.")
        else:
            logger.error(f"EmailJS API Error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Request Error: {e}")