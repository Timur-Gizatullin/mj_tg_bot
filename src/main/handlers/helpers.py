import os

import django
import langdetect
import openai
from aiogram import Bot, types
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.enums import AnswerTypeEnum, PriceEnum, UserRoleEnum, UserStateEnum
from main.models import Channel, OptionPrice, TelegramAnswer
from main.utils import callback_data_util
from t_bot.settings import TELEGRAM_TOKEN

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

TRANSLATOR_GPT_OPTION = (
    "You are a professional translator from Russian into English, "
    "everything that is said to you, you translate into English"
    "If you get message in english, just send it back, do not translate"
)

bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


async def is_enough_balance(telegram_user, amount, message=None, callback=None):
    reply = """Ваш баланс {}.

💰 Вам доступно только  5 бесплатных токенов ежедневно. 

🌇Пополни свой счёт и получи быстрые генерации без очереди! 🎆

💤 Или возвращайтесь завтра!
"""

    if not message:
        if telegram_user.balance - amount < 0:
            builder = InlineKeyboardBuilder()
            lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
            builder.row(*lk_buttons)
            await callback.message.answer(reply.format(telegram_user.balance), reply_markup=builder.as_markup())
            try:
                await check_subs(telegram_user, callback.message)
            except Exception as e:
                logger.error(e)
            telegram_user.state = UserStateEnum.READY
            await telegram_user.asave()
            await callback.answer()
            return False

        return True
    else:
        builder = InlineKeyboardBuilder()
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await message.answer(reply.format(telegram_user.balance), reply_markup=builder.as_markup())

        try:
            await check_subs(telegram_user, message)
        except Exception as e:
            logger.error(e)
        telegram_user.state = UserStateEnum.READY
        await telegram_user.asave()
        return


async def check_subs(telegram_user, message):
    channels: list[Channel] = await Channel.objects.get_all_channels()

    builder = InlineKeyboardBuilder()

    is_subscribed = True
    for channel in channels:
        member = await bot.get_chat_member(f"@{channel.channel}", int(telegram_user.chat_id))
        if member.status == ChatMemberStatus.LEFT:
            is_subscribed = False
        builder.row(types.InlineKeyboardButton(text=f"{channel.channel}", url=f"{channel.link}"))
    builder.row(types.InlineKeyboardButton(text="Я подписался!", callback_data="sub_checkin"))
    if not is_subscribed:
        reply = (
            "Хочешь получать 5 токенов ежедневно? 🪙\n\n" "Подпишись и оставайся в наших интересных и полезных каналах!"
        )
        await message.answer(text=reply, reply_markup=builder.as_markup())


async def is_ready(telegram_user, callback):
    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return False
    if telegram_user.state == UserStateEnum.BANNED:
        await callback.message.answer("🛑 Ваш аккаунт был ограничен, обратитесь к администратору")
        await callback.answer()
        return False

    return True


async def is_can_use(telegram_user, callback, amount):
    if not await is_enough_balance(telegram_user=telegram_user, callback=callback, amount=amount):
        return False

    if not await is_ready(telegram_user, callback):
        return False

    return True


async def gpt_translate(message):
    locale = langdetect.detect(message)
    if locale == "en":
        prompt = message
    else:
        messages = [
            {
                "role": "system",
                "content": TRANSLATOR_GPT_OPTION,
            },
            {"role": "user", "content": message},
        ]

        prompt = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=messages)
        prompt = prompt.choices[0].message.content

    return prompt


async def get_gpt_prompt_suggestions(prompt, callback, user, data):
    messages = [
        {"role": "system", "content": await TelegramAnswer.objects.get_message_by_type(AnswerTypeEnum.GPT_OPTION)},
        {"role": "user", "content": prompt},
    ]
    try:
        await callback.message.answer("Идет генерация ...")
        prompt_suggestions = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=messages)

        builder = InlineKeyboardBuilder()
        buttons = [
            types.InlineKeyboardButton(
                text=f"промпт {i}",
                callback_data=f"choose-gpt_{i}_{callback.message.chat.id}{callback.message.message_id}",
            )
            for i in range(1, 4)
        ]
        builder.row(*buttons)

        logger.debug(data["img"])
        if data["img"]:
            callback_data_util[f"img{callback.message.chat.id}{callback.message.message_id}"] = data["img"]
            logger.debug(callback_data_util)

        await callback.message.answer(
            text=prompt_suggestions.choices[0].message.content, reply_markup=builder.as_markup()
        )

        option_price: OptionPrice = await OptionPrice.objects.get_price_by_product(PriceEnum.gpt)
        user.balance -= option_price.price
        if user.balance < 5 and user.role != UserRoleEnum.ADMIN:
            user.role = UserRoleEnum.BASE
        user.state = UserStateEnum.READY
        await user.asave()
        await callback.message.answer(text=f"Баланс в токенах: {user.balance}")
    except Exception as e:
        logger.error(e)
        user.state = UserStateEnum.READY
        await user.asave()
        await callback.message.answer("Что-то пошло не так :(")
