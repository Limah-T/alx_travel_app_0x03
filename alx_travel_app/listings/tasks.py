from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email(name, email):
    send_mail(
        subject="Booking Confirmation",
        message=f"Hello {name}, your booking has been confirmed",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=True
    )
    # Perform your long-running operation here
    print(f"Sending email to {email}")
    return "Email sent!"