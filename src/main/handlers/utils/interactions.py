from typing import Any

import requests
from loguru import logger

from main.handlers.utils.mj_user import MjUserTokenQueue
from main.models import Blend, Prompt
from t_bot.settings import CHANNEL_ID, GUILD_ID

INTERACTION_URL = "https://discord.com/api/v9/interactions"
ATTACHMENTS_URL = "https://discord.com/api/v9/channels/1160854172049080415/attachments"
MESSAGES_URL = "https://discord.com/api/v9/channels/1160854172049080415/messages"

mj_user_token_queue = MjUserTokenQueue()


def _trigger_payload(type_: int, data: dict[str, Any], **kwargs) -> dict[str, Any]:
    payload = {
        "type": type_,
        "application_id": "936929561302675456",
        "guild_id": GUILD_ID,
        "channel_id": CHANNEL_ID,
        "session_id": "cb06f61453064c0983f2adae2a88c223",
        "data": data,
    }
    payload.update(kwargs)
    return payload


async def send_variation_trigger(variation_index: str, queue: Prompt) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::variation::{variation_index}::{queue.message_hash}"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_upsample_trigger(upsample_index: str, queue: Prompt, version: str = "") -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    solo = "::SOLO" if version != "" else ""
    payload = _trigger_payload(
        3,
        {"component_type": 2, "custom_id": f"MJ::JOB::upsample{version}::{upsample_index}::{queue.message_hash}{solo}"},
        **kwargs,
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_reset_trigger(message_id: str, message_hash: str) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::reroll::0::{message_hash}::SOLO"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_vary_trigger(vary_type: str, queue: Prompt) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::{vary_type}::1::{queue.message_hash}::SOLO"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_zoom_trigger(zoomout: str, queue: Prompt) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3,
        {"component_type": 2, "custom_id": f"MJ::Outpaint::{int(float(zoomout) * 50)}::1::{queue.message_hash}::SOLO"},
        **kwargs,
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_pan_trigger(direction: str, queue: Prompt) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::pan_{direction}::1::{queue.message_hash}::SOLO"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def imagine_trigger(message, prompt):
    payload = _trigger_payload(
        2,
        {
            "version": "1166847114203123795",
            "id": "938956540159881230",
            "name": "imagine",
            "type": 1,
            "options": [{"type": 3, "name": "prompt", "value": f"#{message.chat.id}# {prompt}"}],
            "attachments": [],
        },
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    help_message = (
        "Кнопки U1, U2, U3, U4 - предназначены для увеличения "
        "картинки под соответсвующим номером в высоком разрешении;\n"
        "Кнопки V1, V2, V3, V4 - предназначены для генерации 4 новых "
        "изображений исходной с картинкой под соответсвующим номером;\n"
        "Кнопка предназначена для генерации 4 новых изображений отличающихся по стилистике от первой генерации."
    )

    await message.answer(help_message)

    requests.post(INTERACTION_URL, json=payload, headers=header)


async def describe_reset_trigger(message_id: str):
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(3, {"component_type": 2, "custom_id": "MJ::Picread::Retry"}, **kwargs)
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def blend_trigger(blends: list[Blend]):
    attachments = []
    for blend in blends:
        attachments.append(
            {
                "id": "0",
                "filename": blend.uploaded_filename.split("/")[-1],
                "uploaded_filename": blend.uploaded_filename,
            }
        )

    payload = _trigger_payload(
        2,
        {
            "version": "1166847114203123796",
            "id": "1062880104792997970",
            "name": "blend",
            "type": 1,
            # "options": [{"type": 11, "name": "image1", "value": 0}, {"type": 11, "name": "image2", "value": 1}],
            "attachments": attachments,
        },
    )

    logger.debug(payload)

    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)
    logger.debug(response.text)
