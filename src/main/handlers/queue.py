import json
from datetime import datetime

import requests
from aiogram import Bot
from aiogram.enums import ParseMode
from loguru import logger
from redis import Redis

from main.enums import PriceEnum, UserRoleEnum, UserStateEnum
from main.handlers.utils.const import INTERACTION_URL
from main.models import OptionPrice, Price, User
from t_bot.caches import CONFIG_REDIS_HOST, CONFIG_REDIS_PASSWORD
from t_bot.settings import TELEGRAM_TOKEN

r_queue = Redis(host=CONFIG_REDIS_HOST, password=CONFIG_REDIS_PASSWORD)

bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


class QueueHandler:
    @staticmethod
    async def exclude_queue(chat_id, telegram_user):
        if telegram_user.role == UserRoleEnum.ADMIN:
            await admin_mj_exclude(telegram_user, chat_id)
        else:
            await base_exclude(chat_id, telegram_user)

    @staticmethod
    async def include_queue(payload, header, message, action):
        logger.debug(r_queue.llen("queue"))

        user: User = await User.objects.get_user_by_chat_id(message.chat.id)
        user.state = UserStateEnum.PENDING
        user.pending_state_at = datetime.now()
        await user.asave()

        if user.role == UserRoleEnum.ADMIN:
            await admin_mj_release(payload, header, message, action)
        else:
            if r_queue.llen("queue") >= 3:
                data = json.dumps(
                    {
                        "payload": payload,
                        "header": header,
                        "action": action,
                        "chat_id": message.chat.id,
                        "start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                r_queue.rpush("release", data)

                await message.answer(text="Запрос добавлен в очередь")
            else:
                await base_release(payload, header, action, message, user)


async def admin_mj_release(payload, header, message, action):
    data = json.dumps(
        {
            "chat_id": message.chat.id,
            "action": action,
            "start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    r_queue.rpush(f"admin", message.chat.id)
    r_queue.rpush(f"{message.chat.id}", data)

    response = requests.post(INTERACTION_URL, json=payload, headers=header)
    logger.debug(response.text)
    if response.ok:
        await message.answer(text="Идет генерация... ⌛")
    else:
        await message.answer(text="Не удалось добавить запрос в очередь, попробуйте еще раз")


async def base_release(payload, header, action, message, user):
    data = json.dumps(
        {
            "payload": payload,
            "header": header,
            "action": action,
            "chat_id": message.chat.id,
            "start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    r_queue.rpush(f"queue", message.chat.id)
    r_queue.rpush(f"{message.chat.id}", data)

    response = requests.post(INTERACTION_URL, json=payload, headers=header)
    logger.debug(response.text)
    if response.ok:
        await message.answer(text="Идет генерация... ⌛")
    else:
        user.state = UserStateEnum.READY
        await user.asave()
        await message.answer(text="Не удалось добавить запрос в очередь, попробуйте еще раз")


async def admin_mj_exclude(user: User, chat_id):
    logger.debug(f"Admin QUEUE {r_queue.llen('admin')}")
    r_queue.lrem("admin", 1, chat_id)
    try:
        qdata = json.loads(r_queue.lpop(f"{chat_id}"))
        await update_user(qdata, user)
    except Exception as e:
        logger.error(e)
    if user.role == UserRoleEnum.ADMIN:
        user.state = UserStateEnum.READY
        await user.asave()


async def base_exclude(chat_id, telegram_user):
    logger.debug(f"BASE QUEUE {r_queue.llen('queue')}")
    r_queue.lrem("queue", 1, chat_id)
    try:
        qdata = json.loads(r_queue.lpop(f"{chat_id}"))
        await update_user(qdata, telegram_user)
    except Exception as e:
        logger.error(e)

    try:
        data = json.loads(r_queue.lpop("release"))

        r_queue.rpush("queue", str(chat_id))
        r_queue.rpush(f"{chat_id}", json.dumps(data))
        response = requests.post(INTERACTION_URL, json=data["payload"], headers=data["header"])
        if response.ok:
            await bot.send_message(chat_id=chat_id, text="Идет генерация... ⌛")
        else:
            await bot.send_message(chat_id=chat_id, text="Не удалось добавить запрос в очередь, попробуйте еще раз")
    except Exception as e:
        logger.error(e)


async def update_user(qdata, telegram_user: User):
    telegram_user.fail_in_row = 0
    logger.debug(qdata["action"])
    action = PriceEnum(qdata["action"])
    logger.debug(f"CHECK IN ACTION {action}")
    option_price: OptionPrice = await OptionPrice.objects.get_price_by_product(action)

    telegram_user.balance -= option_price.price

    if telegram_user.balance <= 5 and telegram_user.role != UserRoleEnum.ADMIN:
        telegram_user.role = UserRoleEnum.BASE
    telegram_user.state = UserStateEnum.READY
    await telegram_user.asave()
    logger.debug(telegram_user.state)
