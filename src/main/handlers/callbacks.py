import os

import django
import requests
from aiogram import Router, types

from main.handlers.utils import INTERACTION_URL, _trigger_payload

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import DiscordQueue  # noqa: E402
from t_bot.settings import DISCORD_USER_TOKEN  # noqa: E402

callback_router = Router()


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


@callback_router.callback_query(lambda c: c.data.startswith("V"))
async def callbacks_variations(callback: types.CallbackQuery):
    action = callback.data
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)

    if action == "V1":
        await send_variation_trigger(
            variation_index="1", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )
    elif action == "V2":
        await send_variation_trigger(
            variation_index="2", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )
    elif action == "V3":
        await send_variation_trigger(
            variation_index="3", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )
    elif action == "V4":
        await send_variation_trigger(
            variation_index="4", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("U"))
async def callbacks_upsamples(callback: types.CallbackQuery):
    action = callback.data
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)

    if action == "U1":
        await send_upsample_trigger(
            variation_index="1", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )
    elif action == "U2":
        await send_upsample_trigger(
            variation_index="2", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )
    elif action == "U3":
        await send_upsample_trigger(
            variation_index="3", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )
    elif action == "U4":
        await send_upsample_trigger(
            variation_index="4", message_id=queue.discord_message_id, message_hash=queue.message_hash
        )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("reset"))
async def callback_reset(callback: types.CallbackQuery):
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)

    await send_reset_trigger(message_id=queue.discord_message_id, message_hash=queue.message_hash)

    await callback.answer()
