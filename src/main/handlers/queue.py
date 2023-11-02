import json
from datetime import datetime

import requests
from aiogram import Bot
from aiogram.enums import ParseMode
from loguru import logger
from redis import Redis

from main.enums import UserRoleEnum, UserStateEnum
from main.handlers.utils.const import INTERACTION_URL
from main.models import User
from t_bot.caches import CONFIG_REDIS_HOST, CONFIG_REDIS_PASSWORD
from t_bot.settings import TELEGRAM_TOKEN

r_queue = Redis(host=CONFIG_REDIS_HOST, password=None)

bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


class QueueHandler:
    @staticmethod
    async def exclude_queue(chat_id, telegram_user):
        help_message = (
            "🟢Кнопки U1, U2, U3, U4 - предназначены для увеличения "
            "картинки под соответсвующим номером в высоком разрешении;\n"
            "🔴Кнопки V1, V2, V3, V4 - предназначены для генерации 4 новых "
            "изображений исходной с картинкой под соответсвующим номером;\n"
            "🔁Кнопка предназначена для генерации 4 новых изображений отличающихся по стилистике от первой генерации."
        )

        logger.debug(r_queue.llen("queue"))

        r_queue.lrem("queue", 1, chat_id)

        try:
            qdata = json.loads(r_queue.lpop(f"{chat_id}"))

            if qdata["action"] == "imagine":
                await bot.send_message(chat_id=chat_id, text=help_message)

            logger.debug(qdata["action"])
            if qdata["action"] in (
                "imagine",
                "variation",
                "describe",
                "upsample",
                "reroll",
                "vary",
                "zoom",
                "pan",
                "describe_retry",
            ):
                telegram_user.balance -= 2
                if telegram_user.balance < 5:
                    telegram_user.role = UserRoleEnum.BASE
                telegram_user.state = UserStateEnum.READY
                await telegram_user.asave()
                logger.debug(telegram_user.state)
            elif qdata["action"] in ("upscale_2x", "upscale_4x"):
                if qdata["action"].split("_")[-1] == "2x":
                    cost = 4
                else:
                    cost = 8
                telegram_user.balance -= cost
                if telegram_user.balance < 5:
                    telegram_user.role = UserRoleEnum.BASE
                telegram_user.state = UserStateEnum.READY
                await telegram_user.asave()
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

    @staticmethod
    async def include_queue(payload, header, message, action):
        logger.debug(r_queue.llen("queue"))

        user: User = await User.objects.get_user_by_chat_id(message.chat.id)
        user.state = UserStateEnum.PENDING
        await user.asave()

        if r_queue.llen("queue") >= 3:
            data = json.dumps({"payload": payload, "header": header, "action": action, "chat_id": message.chat.id, "start": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            r_queue.rpush("release", data)

            await message.answer(text="Запрос добавлен в очередь")
        else:
            data = json.dumps({"payload": payload, "header": header, "action": action, "chat_id": message.chat.id, "start": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            r_queue.rpush(f"queue", message.chat.id)
            r_queue.rpush(f"{message.chat.id}", data)

            response = requests.post(INTERACTION_URL, json=payload, headers=header)
            if response.ok:
                await message.answer(text="Идет генерация... ⌛")
            else:
                await message.answer(text="Не удалось добавить запрос в очередь, попробуйте еще раз")
