import os
from mailersend import emails
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API_KEY = os.getenv("MAILERSEND_API_KEY")
SENDER_EMAIL = os.getenv("MAILERSEND_SENDER")

def send_email(to_email, subject, body):
    """
    Sends an email using MailerSend SDK.
    """
    if not API_KEY:
        print("❌ MAILERSEND_API_KEY not found in environment variables")
        return
    
    if not SENDER_EMAIL:
        print("❌ MAILERSEND_SENDER not found in environment variables")
        return

    print(f"📧 Attempting to send email to: {to_email}")

    mailer = emails.NewEmails(API_KEY)

    mail_from = {
        "name": "Zero Trust Security",
        "email": SENDER_EMAIL,
    }

    recipients = [
        {
            "name": "Security User",
            "email": to_email,
        }
    ]

    mail_body = {}

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject, mail_body)
    mailer.set_html_content(f"<div style='font-family: Arial; padding: 20px; border: 1px solid #ddd; border-radius: 8px;'><h2>{subject}</h2><p>{body}</p></div>", mail_body)
    mailer.set_plaintext_content(body, mail_body)

    try:
        # The SDK returns the raw response or errors out
        response = mailer.send(mail_body)
        print(f"✅ Email Sent! Response: {response}")
    except Exception as e:
        print(f"❌ MailerSend Error: {e}")