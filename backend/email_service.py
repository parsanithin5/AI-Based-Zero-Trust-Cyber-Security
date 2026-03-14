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

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())