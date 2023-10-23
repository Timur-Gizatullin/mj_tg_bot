from typing import Any

import requests

from main.handlers.utils.mj_user import MjUserTokenQueue
from main.models import Prompt
from t_bot.settings import CHANNEL_ID, GUILD_ID

INTERACTION_URL = "https://discord.com/api/v9/interactions"

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
        3, {"component_type": 2, "custom_id": f"MJ::JOB::upsample{version}::{upsample_index}::{queue.message_hash}{solo}"}, **kwargs
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
        {"component_type": 2, "custom_id": f"MJ::Outpaint::{int(float(zoomout)*50)}::1::{queue.message_hash}::SOLO"},
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
