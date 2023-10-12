import os

import django
from aiogram import Router, types

from main.handlers.utils import (
    send_pan_trigger,
    send_reset_trigger,
    send_upsample_trigger,
    send_variation_trigger,
    send_vary_trigger,
    send_zoom_trigger,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import DiscordQueue  # noqa: E402

callback_router = Router()


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


@callback_router.callback_query(lambda c: c.data.startswith("vary"))
async def callback_vary(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)

    if action == "strong":
        await send_vary_trigger(
            message_id=queue.discord_message_id, message_hash=queue.message_hash, vary_type="high_variation"
        )
    elif action == "subtle":
        await send_vary_trigger(
            message_id=queue.discord_message_id, message_hash=queue.message_hash, vary_type="low_variation"
        )
    elif action == "region":
        await send_vary_trigger(
            message_id=queue.discord_message_id, message_hash=queue.message_hash, vary_type="variation"
        )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("zoom"))
async def callback_zoom(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)

    if action == "2":
        await send_zoom_trigger(message_id=queue.discord_message_id, message_hash=queue.message_hash, zoomout=action)
    elif action == "1.5":
        await send_zoom_trigger(message_id=queue.discord_message_id, message_hash=queue.message_hash, zoomout=action)
    elif action == "custom":
        # TODO
        pass

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("pan"))
async def callback_pan(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)

    await send_pan_trigger(message_id=queue.discord_message_id, message_hash=queue.message_hash, direction=action)

    await callback.answer()
