from celery import shared_task
from django.core.mail import send_mail
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.template.loader import render_to_string
from django.conf import settings
import os, smtplib, ssl

host = os.environ.get("EMAIL_HOST")
port = int(os.environ.get("EMAIL_PORT"))
sender_email = os.environ.get("EMAIL_HOST_USER")
password = os.environ.get("EMAIL_HOST_PASSWORD")

# @shared_task
def email_verification(subject, email, txt_template_name, verification_url):
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject
    text = render_to_string(txt_template_name, {"verification_url": verification_url})
    msg.attach(MIMEText(text, "plain"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(host=host, port=port, timeout=60, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, email, msg.as_string())
            return True
    except smtplib.SMTPAuthenticationError as e:
        print("❌ Authentication failed:", e)
        return False
    except smtplib.SMTPConnectError as e:
        print("❌ Connection error:", e)
        return False
    except smtplib.SMTPServerDisconnected as e:
        print("❌ Server unexpectedly disconnected:", e)
        return False
    except smtplib.SMTPException as e:
        print("❌ General SMTP error:", e)
        return False
    except ssl.SSLError as e:
        print("❌ SSL error:", e)
        return False
    except TimeoutError as e:
        print("❌ Timeout error:", e)
        return False
    except Exception as e:
        print("❌ Unexpected error:", type(e).__name__, e)
        return False

