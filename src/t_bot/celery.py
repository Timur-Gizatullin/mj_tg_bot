import json
import logging
import os
from datetime import datetime, timedelta

import requests
from celery import Celery
from django.conf import settings

from t_bot.settings import TELEGRAM_TOKEN

logger = logging.getLogger("django")

# Set the default Django settings module for the 'celery' program.
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.enums import UserRoleEnum, UserStateEnum
from main.handlers.queue import r_queue
from main.handlers.utils.wallet import WALLET_CREATE_ORDER, WALLET_HEADERS
from main.models import Pay, User

app = Celery("t_bot")


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(90.0, check_pays.s())
    sender.add_periodic_task(10.0, check_queue.s())


@app.task()
def check_queue():
    queue = r_queue.lrange("queue", 0, -1)
    time = len(queue) * 30 + 120
    logger.info(len(queue))
    for chat_id in queue:
        j_chat_id = json.loads(chat_id)
        queue_data = r_queue.lrange(j_chat_id, 0, -1)
        queue_data = json.loads(queue_data[-1])
        start = queue_data["start"]
        diff = datetime.now() - datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        logger.info(diff)
        if diff >= timedelta(seconds=time):
            user = User.objects.filter(chat_id=j_chat_id).first()
            user.state = UserStateEnum.READY
            user.save()
            r_queue.lpop("queue", j_chat_id)


@app.task()
def check_pays():
    unverified_pays: list[Pay] = Pay.objects.get_unverified_pays()

    for unverified_pay in unverified_pays:
        response = requests.get(f"{WALLET_CREATE_ORDER}?id={unverified_pay.pay_id}", headers=WALLET_HEADERS)
        logger.debug(response.text)
        if response.ok:
            unverified_pay.is_verified = True
            unverified_pay.user.balance += unverified_pay.token_count
            unverified_pay.save()
            message = f"Транзакция прошла успешно, ваш баланс {unverified_pay.user.balance}"
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={unverified_pay.user.chat_id}&text={message}"
            )
            if unverified_pay.user.balance > 5:
                unverified_pay.user.role = UserRoleEnum.BASE
            else:
                unverified_pay.user.role = UserRoleEnum.PREMIUM


app.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
