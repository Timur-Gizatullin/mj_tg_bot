import json

import requests
from aiogram import Bot
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from translate import Translator

from main.enums import UserRoleEnum
from main.handlers.utils.const import ATTACHMENTS_URL
from main.models import User, DsMjUser

host = "http://185.209.22.145:8000"
user_uri = "admin/main/user/{}/change/"


async def is_has_censor(message: str, censor_list: list[str]) -> bool:
    message = message.lower()
    message = message.replace(" ", "")

    for censor_word in censor_list:
        if message.find(censor_word.lower()) != -1:
            return True

    return False


translator = Translator(from_lang="ru", to_lang="en")


async def upload_file(file, header: dict[str, str], chat_id):
    splited_path = file.file_path.split(".")
    file_name = f"{splited_path[0]}{chat_id}.{splited_path[1]}"
    payload = {"files": [{"filename": file_name, "file_size": file.file_size, "id": "0"}]}
    logger.error(payload)

    response = requests.post(ATTACHMENTS_URL, data=json.dumps(payload), headers=header)
    attachment = response.json()["attachments"][0] if response.status_code == 200 else None

    return attachment


async def put_file(attachment, downloaded_file):
    headers = {"Content-Type": "image/png"}
    return requests.put(attachment["upload_url"], data=downloaded_file, headers=headers)


async def notify_admins(bot: Bot, banned_user: User | None = None, banned_mj_user: DsMjUser | None = None):
    admins: list[User] = await User.objects.get_admins()
    if banned_user:
        message = f"Пользователь с чат ID *{banned_user.chat_id}* был забанен автоматически \nссылка на пользователя: {host}/{user_uri.format(banned_user.pk)}"
    else:
        message = f"Аккаунт миджорни с ID *{banned_mj_user.pk}* был забанен, пожалуйста проверьте"
    for admin in admins:
        await bot.send_message(chat_id=admin.chat_id, text=message)


class BlendStateMachine(StatesGroup):
    image = State()
    blend = State()


class MenuState(StatesGroup):
    mj = State()
    gpt = State()
    dalle = State()


callback_data_util = {}
