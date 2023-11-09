import os

import django
import requests
from aiogram import Router, types
from aiogram.enums import ChatMemberStatus
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.enums import UserRoleEnum
from main.handlers.utils.wallet import WALLET_HEADERS, WALLET_PREVIEW_LINK, get_pay_link
from main.handlers.utils.yookassa import create_yookassa_invoice, is_payment_succeeded
from main.keyboards.pay import get_inline_keyboard_from_buttons

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import Channel, Pay, User  # noqa: E402

pay_router = Router()


@pay_router.callback_query(lambda c: c.data.startswith("pay_choose"))
async def callback_pay(callback: types.CallbackQuery):
    action = callback.data.split("_")[-3]
    amount = callback.data.split("_")[-2]
    token = callback.data.split("_")[-1]
    desc = "Get tokens for Mid Journey telegram bot"

    usdt_amount = str(float(amount) / 100)
    logger.debug(action)
    if action == "wallet":
        pay_link, pay_id = await get_pay_link(
            amount=usdt_amount,
            description=desc,
            customer_id=str(callback.from_user.id),
            chat_id=str(callback.message.chat.id),
            token_count=int(token),
            externalId=str(callback.message.message_id),
        )

        if not pay_link:
            await callback.message.answer("Что-то пошло не так :(")
            await callback.answer()
            return

        pay_button = types.InlineKeyboardButton(text="👛 Pay via Wallet", url=pay_link)
        confirm_button = types.InlineKeyboardButton(text="Я оплатил", callback_data=f"confirm-pay_wallet_{pay_id}")
        key_board = get_inline_keyboard_from_buttons((pay_button, confirm_button))

        await callback.message.answer(f"Get {token} tokens for {usdt_amount}$", reply_markup=key_board)
        await callback.answer()
    if action == "yokasa":
        logger.error(amount)
        try:
            user = await User.objects.get_user_by_chat_id(callback.message.chat.id)
            payment_invoice, pay_id = await create_yookassa_invoice(
                amount=str(float(amount)), description=desc, token_count=int(token), user=user
            )
            confirmation_url = payment_invoice["confirmation"]["confirmation_url"]
            pay_button = types.InlineKeyboardButton(text="👛 Pay via Yookassa", url=confirmation_url)
            confirm_button = types.InlineKeyboardButton(
                text="Я оплатил", callback_data=f"confirm-pay_yookassa_{pay_id}"
            )
            key_board = get_inline_keyboard_from_buttons((pay_button, confirm_button))
            await callback.message.answer(f"Get {token} tokens for {amount}₽", reply_markup=key_board)
            await callback.answer()
        except Exception as e:
            logger.error(e)
            await callback.message.answer("Не удалось создать платеж")
            await callback.answer()


@pay_router.callback_query(lambda c: c.data.startswith("confirm-pay"))
async def callbacks_confirm_pay(callback: types.CallbackQuery):
    action = callback.data.split("_")[-2]
    pay_id = callback.data.split("_")[-1]
    user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if action == "yookassa":
        pay_dto: Pay = await Pay.objects.get_unverified_pay_by_id(pay_id)

        if not pay_dto:
            await callback.message.answer("Не удалось найти платеж")
            await callback.answer()
            return

        is_succeeded = await is_payment_succeeded(pay_dto.pay_id)

        if is_succeeded:
            pay_dto.is_verified = True
            user.balance += pay_dto.token_count
            await pay_dto.asave()
            await user.asave()

            message = f"Транзакция прошла успешно, ваш баланс {user.balance}"
            await callback.message.answer(message)
        else:
            await callback.message.answer("Платеж обрабатывается или отменен, попробуйте позже")
            await callback.answer()
            return

    if action == "wallet":
        pay_dto: Pay = await Pay.objects.get_unverified_pay_by_id(pay_id)

        if not pay_dto:
            await callback.message.answer("Не удалось найти платеж")
            await callback.answer()
            return

        response = requests.get(f"{WALLET_PREVIEW_LINK}?id={pay_dto.pay_id}", headers=WALLET_HEADERS)
        logger.debug(response.text)
        if response.ok:
            pay_dto.is_verified = True
            user.balance += pay_dto.token_count
            await pay_dto.asave()
            await user.asave()
            message = f"Транзакция прошла успешно, ваш баланс {user.balance}"
            await callback.message.answer(message)
        else:
            await callback.message.answer("Платеж обрабатывается или отменен, попробуйте позже")
            await callback.answer()
            return

    if user.balance < 5:
        user.role = UserRoleEnum.BASE
    else:
        user.role = UserRoleEnum.PREMIUM


@pay_router.callback_query(lambda c: c.data.startswith("pay-options"))
async def pay_options_callback(callback: types.CallbackQuery):
    token = callback.data.split("_")[1]
    amount = callback.data.split("_")[-1]

    answer = f"Выберите способ оплаты"
    builder = InlineKeyboardBuilder()
    buttons = (
        types.InlineKeyboardButton(
            text="Любой картой РФ (Юкасса)", callback_data=f"pay_choose_yokasa_{amount}_{token}"
        ),
        types.InlineKeyboardButton(text="Telegram Wallet", callback_data=f"pay_choose_wallet_{amount}_{token}"),
    )
    for button in buttons:
        builder.row(button)

    await callback.message.answer(answer, reply_markup=builder.as_markup())
    await callback.answer()


@pay_router.callback_query(lambda c: c.data.startswith("sub"))
async def pay_options_callback(callback: types.CallbackQuery):
    action = callback.data.split("_")[-1]

    channels: list[Channel] = await Channel.objects.get_all_channels()

    if action == "checkin":
        is_subscribed = True
        for channel in channels:
            member = await callback.bot.get_chat_member(f"@{channel.channel}", int(callback.message.chat.id))
            if member.status == ChatMemberStatus.LEFT:
                is_subscribed = False
                break

        if is_subscribed:
            user = await User.objects.get_user_by_chat_id(callback.message.chat.id)
            user.balance += 5
            await user.asave()
            reply = (
                "🎉 🎉🎉Поздравляем! Пока Вы подписаны на наши каналы, "
                "Вам будут начисляться 5 бесплатных токенов ежедневно!"
            )
        else:
            reply = "🚨🚨🚨 пожалуйста подпишитесь на наши каналы, и Вы будtте получать  5 токенов ежедневно."

        await callback.message.answer(text=reply)
