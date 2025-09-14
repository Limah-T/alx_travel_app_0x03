from celery import shared_task
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.template.loader import render_to_string
import os, smtplib, ssl, logging

logger = logging.getLogger(__name__)

host = os.environ.get("EMAIL_HOST")
port = int(os.environ.get("EMAIL_PORT"))
sender_email = os.environ.get("EMAIL_HOST_USER")
password = os.environ.get("EMAIL_HOST_PASSWORD")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def email_verification(self, subject, email, txt_template_name, verification_url):
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject
    text = render_to_string(txt_template_name, {"verification_url": verification_url})
    msg.attach(MIMEText(text, "plain"))
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(host=host, port=port, timeout=30, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, email, msg.as_string())
    except Exception as exc:
        logger.error("Error retrying..", exc)
        raise self.retry(exc=exc)

    
