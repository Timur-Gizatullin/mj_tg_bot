import os

import django
from aiogram import Router, types

from main.handlers.queue import queue_handler
from main.handlers.utils.interactions import (
    send_pan_trigger,
    send_reset_trigger,
    send_upsample_trigger,
    send_variation_trigger,
    send_vary_trigger,
    send_zoom_trigger,
)
from main.handlers.utils.wallet import get_pay_link
from main.keyboards.pay import get_gen_count, get_inline_keyboard_from_buttons

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import Prompt, User  # noqa: E402

callback_router = Router()


@callback_router.callback_query(lambda c: c.data.startswith("V"))
async def callbacks_variations(callback: types.CallbackQuery):
    action = callback.data
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user: User = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "V1":
        await queue_handler.add_task(
            send_variation_trigger, variation_index="1", queue=queue, user_role=telegram_user.role
        )
    elif action == "V2":
        await queue_handler.add_task(
            send_variation_trigger, variation_index="2", queue=queue, user_role=telegram_user.role
        )
    elif action == "V3":
        await queue_handler(send_variation_trigger, variation_index="3", queue=queue, user_role=telegram_user.role)
    elif action == "V4":
        await queue_handler.add_task(
            send_variation_trigger, variation_index="4", queue=queue, user_role=telegram_user.role
        )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("_v5"))
async def callbacks_upsamples_v5(callback: types.CallbackQuery):
    action = callback.data
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    await queue_handler.add_task(
        send_upsample_trigger, upsample_index="1", queue=queue, version=action, user_role=telegram_user.role
    )


@callback_router.callback_query(lambda c: c.data.startswith("U"))
async def callbacks_upsamples(callback: types.CallbackQuery):
    action = callback.data
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "U1":
        await queue_handler.add_task(
            send_upsample_trigger, upsample_index="1", queue=queue, user_role=telegram_user.role
        )
    elif action == "U2":
        await queue_handler.add_task(
            send_upsample_trigger, upsample_index="2", queue=queue, user_role=telegram_user.role
        )
    elif action == "U3":
        await queue_handler.add_task(
            send_upsample_trigger, upsample_index="3", queue=queue, user_role=telegram_user.role
        )
    elif action == "U4":
        await queue_handler.add_task(
            send_upsample_trigger, upsample_index="4", queue=queue, user_role=telegram_user.role
        )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("reset"))
async def callback_reset(callback: types.CallbackQuery):
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    await queue_handler.add_task(
        send_reset_trigger,
        message_id=queue.discord_message_id,
        message_hash=queue.message_hash,
        user_role=telegram_user.role,
    )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("vary"))
async def callback_vary(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "strong":
        await queue_handler.add_task(
            send_vary_trigger, vary_type="high_variation", queue=queue, user_role=telegram_user.role
        )
    elif action == "subtle":
        await queue_handler.add_task(
            send_vary_trigger, vary_type="low_variation", queue=queue, user_role=telegram_user.role
        )
    elif action == "region":
        pass  # TODO

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("zoom"))
async def callback_zoom(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if action == "2":
        await queue_handler.add_task(send_zoom_trigger, queue=queue, zoomout=action, user_role=telegram_user.role)
    elif action == "1.5":
        await queue_handler.add_task(send_zoom_trigger, queue=queue, zoomout=action, user_role=telegram_user.role)
    elif action == "custom":
        pass

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("pan"))
async def callback_pan(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    await queue_handler.add_task(send_pan_trigger, queue=queue, direction=action, user_role=telegram_user.role)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("mjpay"))
async def callback_mj_pay(callback: types.CallbackQuery):
    amount = f"{callback.data.split('_')[1]}.00"
    desc = "Get descriptions from mid journey on your telegram account"

    pay_link = await get_pay_link(amount=amount, description=desc, customer_id=str(callback.from_user.id))

    if not pay_link:
        await callback.message.answer("Что-то пошло не так :(")
        await callback.answer()
        return

    pay_button = types.InlineKeyboardButton(text="👛 Pay via Wallet", url=pay_link)
    key_board = get_inline_keyboard_from_buttons((pay_button,))

    gen_count = get_gen_count(amount=amount)

    await callback.message.answer(
        f"Get {gen_count} prompts for {amount}$\n<b>Enjoy!</b>",
        reply_markup=key_board,
    )
    await callback.answer()
