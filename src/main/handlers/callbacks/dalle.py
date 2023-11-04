import openai
import requests
from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.enums import AnswerTypeEnum, UserRoleEnum, UserStateEnum
from main.handlers.commands import bot, gpt
from main.handlers.routers import (
    GPT_OPTION,
    gpt_translate,
    is_can_use,
    is_enough_balance,
    is_ready,
)
from main.keyboards.commands import resources
from main.models import BanWord, TelegramAnswer, User
from main.utils import callback_data_util, is_has_censor

dalle_router = Router()


@dalle_router.callback_query(lambda c: c.data.startswith("dalle"))
async def dalle_suggestion_callback(callback: types.CallbackQuery):
    action = callback.data.split("_")[2]
    message_id = callback.data.split("_")[-1]
    message = callback_data_util.get(message_id)
    if not message:
        await callback.message.answer("Сообщение удалено из кэша, введите ваш промпт снова")
        await callback.answer()
        return
    user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if not await is_ready(user, callback):
        return
    user.state = UserStateEnum.PENDING
    await user.asave()

    prompt = await gpt_translate(message)

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message and await is_has_censor(prompt, ban_words):
        await callback.message.answer(censor_message_answer)
        user.state = UserStateEnum.READY
        await user.asave()
        return

    try:
        if action == "gpt":
            if not await is_enough_balance(user, callback, 1):
                return

            messages = [
                {"role": "system", "content": GPT_OPTION},
                {"role": "user", "content": prompt},
            ]
            answer = await callback.message.answer(f"GPT думает ... ⌛\n")
            prompt_suggestions = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)

            builder = InlineKeyboardBuilder()
            buttons = [
                types.InlineKeyboardButton(text=f"промпт {i}", callback_data=f"choose-dalle-gpt_{i}")
                for i in range(1, 4)
            ]
            builder.row(*buttons)

            user.balance -= 1
            if user.balance < 5:
                user.role = UserRoleEnum.BASE
            user.state = UserStateEnum.READY
            await user.asave()

            await answer.edit_text(text=prompt_suggestions.choices[0].message.content, reply_markup=builder.as_markup())
            await callback.message.answer(text=f"Ваш баланс в токенах: {user.balance}")
            return
        if action == "stay":
            if not await is_enough_balance(user, callback, 2):
                return

            await callback.message.answer("Идет генерация... ⌛\n")
            img_data = await openai.Image.acreate(prompt=prompt, n=1, size="1024x1024")
            img_links = img_data["data"]
            for img_link in img_links:
                raw_image = requests.get(img_link["url"]).content
                img = BufferedInputFile(file=raw_image, filename=f"{callback.message.message_id}.png")
                await bot.send_photo(chat_id=callback.message.chat.id, photo=img, caption=f"`{prompt}`", parse_mode=ParseMode.MARKDOWN)

            user.balance -= 2
            if user.balance < 5:
                user.role = UserRoleEnum.BASE
            user.state = UserStateEnum.READY
            await user.asave()

            await bot.send_message(
                chat_id=callback.message.chat.id, text=f"Баланс в токенах {user.balance}\n\n{resources}"
            )
            return
    except Exception as e:
        logger.error(e)
        user.state = UserStateEnum.READY
        await user.asave()
        await callback.message.answer(f"Не удалось запустить генерацию\nБаланс в токенах {user.balance}")


@dalle_router.callback_query(lambda c: c.data.startswith("choose-dalle-gpt"))
async def gpt_dalle_choose_callback(callback: types.CallbackQuery):
    choose = int(callback.data.split("_")[1])
    telegram_user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if not await is_can_use(telegram_user, callback, 2):
        return
    telegram_user.state = UserStateEnum.PENDING
    await telegram_user.asave()

    try:
        prompt = callback.message.text.split("\n\n")[choose - 1][2:]
    except Exception:
        prompt = callback.message.text.split("\n")[choose - 1][2:]

    try:
        await callback.message.answer(f"Идет генерация... ⌛\n")
        img_data = await openai.Image.acreate(prompt=prompt, n=1, size="1024x1024")
        img_links = img_data["data"]
        for img_link in img_links:
            raw_image = requests.get(img_link["url"]).content
            img = BufferedInputFile(file=raw_image, filename=f"{callback.message.message_id}.png")
            await bot.send_photo(
                chat_id=callback.message.chat.id, photo=img, caption=f"`{prompt}`", parse_mode=ParseMode.MARKDOWN
            )

        telegram_user.balance -= 2
        if telegram_user.balance < 5:
            telegram_user.role = UserRoleEnum.BASE
        telegram_user.state = UserStateEnum.READY
        await telegram_user.asave()
        await bot.send_message(
            chat_id=callback.message.chat.id, text=f"Баланс в токенах {telegram_user.balance}\n\n{resources}"
        )
    except Exception as e:
        logger.error(e)
        telegram_user.state = UserStateEnum.READY
        await telegram_user.asave()
        await callback.message.answer(f"Не удалось запустить генерацию\nБаланс в токенах {telegram_user.balance}")
