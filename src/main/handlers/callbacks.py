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

from main.models import DiscordQueue, User  # noqa: E402

callback_router = Router()


@callback_router.callback_query(lambda c: c.data.startswith("V"))
async def callbacks_variations(callback: types.CallbackQuery):
    action = callback.data
    telegram_chat_id = callback.message.chat.id

    print("callbacks.py")
    print(callback.message)

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "V1":
        await send_variation_trigger(
            variation_index="1", queue=queue, user=telegram_user
        )
    elif action == "V2":
        await send_variation_trigger(
            variation_index="2", queue=queue, user=telegram_user
        )
    elif action == "V3":
        await send_variation_trigger(
            variation_index="3", queue=queue, user=telegram_user
        )
    elif action == "V4":
        await send_variation_trigger(
            variation_index="4", queue=queue, user=telegram_user
        )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("U"))
async def callbacks_upsamples(callback: types.CallbackQuery):
    action = callback.data
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "U1":
        await send_upsample_trigger(
            upsample_index="1", queue=queue, user=telegram_user
        )
    elif action == "U2":
        await send_upsample_trigger(
            upsample_index="2", queue=queue, user=telegram_user
        )
    elif action == "U3":
        await send_upsample_trigger(
            upsample_index="3", queue=queue, user=telegram_user
        )
    elif action == "U4":
        await send_upsample_trigger(
            upsample_index="4", queue=queue, user=telegram_user
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
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "strong":
        await send_vary_trigger(
             vary_type="high_variation", user=telegram_user, queue=queue
        )
    elif action == "subtle":
        await send_vary_trigger(
            vary_type="low_variation", user=telegram_user, queue=queue
        )
    elif action == "region":
        await send_vary_trigger(
            vary_type="variation", user=telegram_user, queue=queue
        )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("zoom"))
async def callback_zoom(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "2":
        await send_zoom_trigger(queue=queue, zoomout=action, user=telegram_user)
    elif action == "1.5":
        await send_zoom_trigger(queue=queue, zoomout=action, user=telegram_user)
    elif action == "custom":
        # TODO
        pass

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("pan"))
async def callback_pan(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    telegram_chat_id = callback.message.chat.id

    queue: DiscordQueue = await DiscordQueue.objects.get_queue_by_telegram_chat_id(telegram_chat_id=telegram_chat_id)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    await send_pan_trigger(queue=queue, direction=action, user=telegram_user)

    await callback.answer()
