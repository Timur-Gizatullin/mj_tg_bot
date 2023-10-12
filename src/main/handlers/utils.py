from typing import Any

import requests

from t_bot.settings import CHANNEL_ID, DISCORD_USER_TOKEN, GUILD_ID

INTERACTION_URL = "https://discord.com/api/v9/interactions"


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


async def send_variation_trigger(variation_index: str, message_id: str, message_hash: str) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::variation::{variation_index}::{message_hash}"}, **kwargs
    )
    header = {"authorization": DISCORD_USER_TOKEN}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_upsample_trigger(variation_index: str, message_id: str, message_hash: str) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::upsample::{variation_index}::{message_hash}"}, **kwargs
    )
    header = {"authorization": DISCORD_USER_TOKEN}

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
    header = {"authorization": DISCORD_USER_TOKEN}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_vary_trigger(message_id: str, message_hash: str, vary_type: str) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::{vary_type}::1::{message_hash}::SOLO"}, **kwargs
    )
    header = {"authorization": DISCORD_USER_TOKEN}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_zoom_trigger(message_id: str, message_hash: str, zoomout: str) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::Outpaint::{zoomout}::1::{message_hash}::SOLO"}, **kwargs
    )
    header = {"authorization": DISCORD_USER_TOKEN}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_pan_trigger(message_id: str, message_hash: str, direction: str) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::pan_{direction}::1::{message_hash}::SOLO"}, **kwargs
    )
    header = {"authorization": DISCORD_USER_TOKEN}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code
