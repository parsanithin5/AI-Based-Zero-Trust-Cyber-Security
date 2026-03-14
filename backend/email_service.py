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
import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

def send_email(to_email: str, subject: str, body: str):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "html": f"<p>{body}</p>",
            },
        )

        if response.status_code == 200 or response.status_code == 202:
            print("✅ Email sent successfully")
        else:
            print("❌ Email failed:", response.text)

    except Exception as e:
        print("❌ Email error:", e)