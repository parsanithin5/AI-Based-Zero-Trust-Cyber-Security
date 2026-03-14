# import smtplib
# import os
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# EMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
# EMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# def send_email(to_email: str, subject: str, body: str):
#     if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
#         print("⚠️ Email credentials not configured")
#         return

#     msg = MIMEMultipart()
#     msg["From"] = EMAIL_ADDRESS
#     msg["To"] = to_email
#     msg["Subject"] = subject
#     msg.attach(MIMEText(body, "plain"))

#     with smtplib.SMTP("smtp.gmail.com", 587) as server:
#         server.starttls()
#         server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
#         server.send_message(msg)
# import os
# import requests

# RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# def send_email(to_email, subject, body):

#     print("📧 Sending email to:", to_email)

#     response = requests.post(
#         "https://api.resend.com/emails",
#         headers={
#             "Authorization": f"Bearer {RESEND_API_KEY}",
#             "Content-Type": "application/json",
#         },
#         json={
#             "from": "onboarding@resend.dev",
#             "to": [to_email],
#             "subject": subject,
#             "html": f"<p>{body}</p>",
#         },
#     )

#     print("📨 Resend response:", response.status_code, response.text)
import requests
import os

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

def send_email(to_email, subject, body):

    if not RESEND_API_KEY:
        print("❌ RESEND_API_KEY not found in environment variables")
        return

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "html": f"<h3>{body}</h3>"
            }
        )

        print("📧 Email response:", response.status_code)
        print("📧 Email response body:", response.text)

    except Exception as e:
        print("❌ Email sending failed:", e)