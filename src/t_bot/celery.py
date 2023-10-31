import logging
import os

import requests
from celery import Celery
from django.conf import settings

from t_bot.settings import TELEGRAM_TOKEN

logger = logging.getLogger("django")

# Set the default Django settings module for the 'celery' program.
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.utils.wallet import WALLET_CREATE_ORDER, WALLET_HEADERS
from main.models import Pay

app = Celery("t_bot")


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, check_pays.s())


@app.task()
def check_pays():
    unverified_pays: list[Pay] = Pay.objects.get_unverified_pays()

    for unverified_pay in unverified_pays:
        response = requests.get(f"{WALLET_CREATE_ORDER}?id={unverified_pay.pay_id}", headers=WALLET_HEADERS)
        logger.debug(response.text)
        if response.ok:
            unverified_pay.is_verified = True
            unverified_pay.save()
            message = f"Транзакция прошла успешно, ваш баланс {unverified_pay.user.balance}"
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={unverified_pay.user.chat_id}&text={message}"
            )


app.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
