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
import smtplib
import os
from email.mime.text import MIMEText

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully")
    except Exception as e:
        print("❌ Email failed:", e)