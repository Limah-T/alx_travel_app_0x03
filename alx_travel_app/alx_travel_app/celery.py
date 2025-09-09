# Reddis conf
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

app = Celery('alx_travel_app')

# Using a string here means the worker doesn't need to pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all installed Django apps.
app.autodiscover_tasks()

        