import json
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.enums import ChatMemberStatus, ParseMode
from asgiref.sync import async_to_sync
from celery import Celery
from django.conf import settings

from t_bot.settings import TELEGRAM_TOKEN

logger = logging.getLogger("django")

# Set the default Django settings module for the 'celery' program.
import django  # noqa:E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.enums import UserRoleEnum, UserStateEnum  # noqa:E402
from main.handlers.queue import r_queue  # noqa:E402
from main.handlers.utils.interactions import mj_user_token_queue  # noqa:E402
from main.models import Channel  # noqa:E402
from main.models import User  # noqa:E402
from main.utils import notify_admins  # noqa:E402

app = Celery("t_bot")
bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

banned_message_answer = """⛔️Возможно Ваш запрос не прошел  модерацию! Пожалуйста пересмотрите текст или приложенное изображение и попробуйте снова! 

Напоминаем запрещенные темы:

1. Насилие (действия, кровь и т.д.)

2. Эротика (части тела, порнографию, обнажение и т.д.)

3. Публичные фигуры в плохом контексте 

4. Расизм"""


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, check_queue.s())
    sender.add_periodic_task(60.0 * 60 * 24, check_subscriptions.s())


@app.task()
def check_subscriptions():
    users: list[User] = list(User.objects.filter(balance__lte=5, role=UserRoleEnum.BASE).all())
    channels: list[Channel] = list(Channel.objects.all())
    logger.debug(len(users))
    logger.debug(len(channels))

    async def task(users, channels):
        logger.debug(channels)
        if channels:
            for user in users:
                for channel in channels:
                    try:
                        logger.warning(f"CHANNEL {channel.channel}")
                        member = await bot.get_chat_member(f"@{channel.channel}", int(user.chat_id))
                        if member.status == ChatMemberStatus.LEFT:
                            break
                        user.balance = 5
                        await user.asave()
                    except Exception as e:
                        logger.warning(e)

    async_to_sync(task)(users, channels)


@app.task()
def check_queue():
    base_queue = r_queue.lrange("queue", 0, -1)
    admin_queue = r_queue.lrange("admin", 0, -1)
    queues = (base_queue, admin_queue)
    time = len(base_queue) * 30 + 120
    logger.info(f"BASE QUEUE LEN: {len(base_queue)}")
    logger.info(f"ADMIN QUEUE LEN: {len(admin_queue)}")

    async def task(base_queue, admin_queue, time, queues):
        for queue in queues:
            for chat_id in queue:
                j_chat_id = json.loads(chat_id)
                queue_data = r_queue.lrange(j_chat_id, 0, -1)
                queue_data = json.loads(queue_data[-1])
                start = queue_data["start"]
                diff = datetime.now() - datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                logger.info(diff)

                if diff >= timedelta(seconds=time):
                    user = await User.objects.get_user_by_chat_id(chat_id=j_chat_id)
                    user.state = UserStateEnum.READY
                    user.fail_in_row += 1
                    await user.asave()

                    await bot.send_message(chat_id=user.chat_id, text=banned_message_answer)

                    await mj_user_token_queue.update_sender(is_fail=True, user=user)

                    if user.fail_in_row >= 10:
                        try:
                            user.state = UserStateEnum.BANNED
                            await user.asave()
                            await notify_admins(bot=bot, banned_user=user)
                        except Exception as e:
                            logger.error(e)

                    if queue is base_queue:
                        r_queue.lpop("queue", j_chat_id)
                    if queue is admin_queue:
                        r_queue.lpop("admin", j_chat_id)

    async_to_sync(task)(base_queue, admin_queue, time, queues)


app.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
