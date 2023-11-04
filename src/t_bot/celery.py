import json
import logging
import os
from datetime import datetime, timedelta

from celery import Celery
from django.conf import settings

logger = logging.getLogger("django")

# Set the default Django settings module for the 'celery' program.
import django  # noqa:E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.enums import UserStateEnum  # noqa:E402
from main.handlers.queue import r_queue  # noqa:E402
from main.models import User  # noqa:E402

app = Celery("t_bot")


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
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


app.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
