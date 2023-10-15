from typing import Any

import requests

from main.models import DiscordQueue, User, MjUser
from t_bot.settings import CHANNEL_ID, GUILD_ID

INTERACTION_URL = "https://discord.com/api/v9/interactions"
unbanned_discord_users: list[MjUser] = MjUser.objects.filter(is_banned=False).all()
unloaded_discord_users: list[MjUser] #TODO remove it to redis


async def get_loaded_discord_user():
    if len(unloaded_discord_users) != 0:
        discord_user = unbanned_discord_users.pop(0)
        unloaded_discord_users.append(discord_user)
        return discord_user
    else:
        unbanned_discord_users.extend(unloaded_discord_users)
        unloaded_discord_users.clear()
        return unbanned_discord_users.pop(0)


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


async def send_variation_trigger(variation_index: str, queue: DiscordQueue, user: User) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::variation::{variation_index}::{queue.message_hash}"}, **kwargs
    )
    header = {"authorization": await get_loaded_discord_user()}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_upsample_trigger(upsample_index: str, queue: DiscordQueue, user: User) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::upsample::{upsample_index}::{queue.message_hash}"}, **kwargs
    )
    header = {"authorization": await get_loaded_discord_user()}

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
    header = {"authorization": await get_loaded_discord_user()}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_vary_trigger(vary_type: str, queue: DiscordQueue, user: User) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::{vary_type}::1::{queue.message_hash}::SOLO"}, **kwargs
    )
    header = {"authorization": await get_loaded_discord_user()}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_zoom_trigger(zoomout: str, queue: DiscordQueue, user: User) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3,
        {"component_type": 2, "custom_id": f"MJ::Outpaint::{int(zoomout)*50}::1::{queue.message_hash}::SOLO"},
        **kwargs,
    )
    header = {"authorization": await get_loaded_discord_user()}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code


async def send_pan_trigger(direction: str, queue: DiscordQueue, user: User) -> int:
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::pan_{direction}::1::{queue.message_hash}::SOLO"}, **kwargs
    )
    header = {"authorization": await get_loaded_discord_user()}

    response = requests.post(INTERACTION_URL, json=payload, headers=header)

    return response.status_code
