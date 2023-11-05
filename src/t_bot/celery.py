import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.enums import ParseMode
from celery import Celery
from django.conf import settings

from t_bot.settings import TELEGRAM_TOKEN

logger = logging.getLogger("django")

# Set the default Django settings module for the 'celery' program.
import django  # noqa:E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.enums import UserStateEnum  # noqa:E402
from main.handlers.queue import r_queue  # noqa:E402
from main.models import User  # noqa:E402

app = Celery("t_bot")
bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, check_queue.s())


@app.task()
def check_queue():
    base_queue = r_queue.lrange("queue", 0, -1)
    admin_queue = r_queue.lrange("admin", 0, -1)
    queues = (base_queue, admin_queue)
    time = len(base_queue) * 30 + 120
    logger.info(f"BASE QUEUE LEN: {len(base_queue)}")
    logger.info(f"ADMIN QUEUE LEN: {len(admin_queue)}")
    for queue in queues:
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

                asyncio.run(bot.send_message(
                    chat_id=user.chat_id, text="Миджорни не пропустил или не смог обработать запрос, попробуйте еще раз"
                ))
                if queue is base_queue:
                    r_queue.lpop("queue", j_chat_id)
                if queue is admin_queue:
                    r_queue.lpop("admin", j_chat_id)


app.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
