import requests
import os

MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")

def send_email(to_email, subject, body):

    if not MAILERSEND_API_KEY:
        print("❌ MAILERSEND_API_KEY not found in environment variables")
        return

    try:
        response = requests.post(
            "https://api.mailersend.com/v1/email",
            headers={
                "Authorization": f"Bearer {MAILERSEND_API_KEY}",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            json={
                "from": {
                    "email": "noreply@test-r9084zv6m0vgw63d.mlsender.net",
                    "name": "Zero Trust Security"
                },
                "to": [
                    {
                        "email": to_email
                    }
                ],
                "subject": subject,
                "text": body,
                "html": f"<h3>{body}</h3>"
            }
        )

        print("📧 MailerSend response:", response.status_code)

        if response.status_code == 202:
            print("✅ Email sent successfully via MailerSend")
        else:
            print("❌ MailerSend error:", response.text)

    except Exception as e:
        print("❌ Email sending failed:", e)