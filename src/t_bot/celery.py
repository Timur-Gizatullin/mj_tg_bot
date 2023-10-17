import logging
import os

from celery import Celery
from django.conf import settings

logger = logging.getLogger("django")

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")

app = Celery("t_bot")

app.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
