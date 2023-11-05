import json

import requests
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from translate import Translator

from main.handlers.utils.const import ATTACHMENTS_URL


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


class BlendStateMachine(StatesGroup):
    image = State()
    blend = State()


class MenuState(StatesGroup):
    mj = State()
    gpt = State()
    dalle = State()


callback_data_util = {}
