import os

import django
from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.constants import BOT_START_HOST
from main.enums import ProductEnum
from main.models import Referral, User
from main.models.prices import Price
from main.utils import MenuState

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

menu_router = Router()


@menu_router.callback_query(lambda c: c.data.startswith("start"))
async def menu_start_callback(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    current_user: User = await User.objects.get_user_by_chat_id(str(callback.message.chat.id))

    if action == "mj":
        intro_message = (
            "🌆Для создания изображения отправь боту только ключевые фразы на русском или английском(не смешивать), раздели их логической запятой;\nНапример:\n"
            "`Бред Пит в роли Терминатор сидит на мотоцикле, огонь на заднем плане`\n\n"
            "❗Порядок слов очень важен! Чем раньше слово, тем сильнее его вес;\n\n"
            "🛑 Не нужно писать  “создай изображение”, это ухудшит результат;\n\n"
            "👨‍🎨 Дорисовать твое изображение\n\n"
            "Отправь картинку боту и напиши промпт в комментарии к ней;\n\n"
            "🖋Описать изображение\n\n"
            "Отправь боту свое изображение без подписи и он пришлет четыре варианта ее описания;\n\n"
            "🌇🎆 Объединить изображение\n\n"
            "Отправь боту твои изображения и он объеденит их.\n"
            "💡Для наилучшей работы функции рекомендуем использовать не более 4 изображений, а так же, одинаковое или близкое соотношение сторон изображения;\n\n"
            "🔞Внимание!!! Строго запрещены запросы изображения 18+, работает AI модератор, несоблюдение правил приведет к бану!"
        )
        await callback.message.answer(intro_message, parse_mode=ParseMode.MARKDOWN)
        await state.set_state(MenuState.mj)
        await callback.answer()
        return
    if action == "dale":
        intro_message = (
            "🌆Для создания изображения отправь боту только ключевые фразы, раздели их логической запятой;\n\n"
            "🔞Внимание!!! Строго запрещены запросы изображения 18+, работает AI модератор, несоблюдение правил приведет к бану!"
        )

        await callback.message.answer(intro_message)
        await state.set_state(MenuState.dalle)
        await callback.answer()
        return
    if action == "gpt":
        answer = (
            "Введи свой запрос.\n\n"
            "Бот поддерживает функционал CHAT GPT, максимальный контекст - 15 запросов.\n\n"
            "📂Для работы с файлами, сначала вставьте ссылку в начале сообщения на файл "
            "(например  Google или Яндекс  диск) и далее укажите что с ним необходимо сделать."
        )
        await callback.message.answer(answer)
        await state.set_state(MenuState.gpt)
        await callback.answer()
        return
    if action == "lk":
        referral: Referral = await Referral.objects.get_referral_by_user(user=current_user)
        if not referral:
            referral = await Referral.objects.create_referral(current_user)

        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {current_user.balance}\n" f"Ваша реферальная ссылка: {BOT_START_HOST}{referral.key}"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

        await callback.answer()
        return
    if action == "ref":
        referral: Referral = await Referral.objects.get_referral_by_user(user=current_user)
        if not referral:
            referral = await Referral.objects.create_referral(current_user)

        answer = (
            "За каждого реферала Вам будет начислено 6 токенов\n\n"
            f"Ваша реферальная ссылка: {BOT_START_HOST}{referral.key}"
        )
        await callback.message.answer(answer, parse_mode=ParseMode.HTML)

        await callback.answer()
        return


@menu_router.callback_query(lambda c: c.data.startswith("lk"))
async def lk_callback(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    current_user: User = await User.objects.get_user_by_chat_id(str(callback.message.chat.id))

    if action == "options":
        answer = (
            f"Ваш баланс в токенах: {current_user.balance}\n"
            "Одна генерация Midjourney = 2\n"
            "Отдельно тарифицируются генерации Upscale:\n"
            "Увеличение базового изображения, зум, изменение масштаьа и тд = 2\n"
            "Upscale 2x = 4\n"
            "Upscale 4x = 8\n"
            "Одна генерация DALL-E = 2\n"
            "Один запрос Chat GPT в т.ч. По формированию промпта = 1\n"
            "При оплате в USDT - 1 usdt = 100р"
        )

        prices: list[Price] = await Price.objects.get_active_prices_by_product(ProductEnum.TOKEN)
        options_button = []
        for price in prices:
            button = types.InlineKeyboardButton(
                text=f"{price.quantity} {price.description} = {price.amount} руб",
                callback_data=f"pay-options_{price.quantity}_{price.amount}",
            )
            options_button.append(button)

        builder = InlineKeyboardBuilder()
        j = 0
        for i in range(len(options_button) // 2):
            builder.row(options_button[j], options_button[j + 1])
            j += 2
        if range(len(options_button) % 2 != 0):
            builder.row(options_button[-1])

        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()


@menu_router.callback_query(lambda c: c.data.startswith("ref_list"))
async def ref_callback(callback: types.CallbackQuery):
    referrals: list[Referral] = await Referral.objects.get_referrals()

    builder = InlineKeyboardBuilder()
    for referral in referrals:
        button = types.InlineKeyboardButton(
            text=f"{referral.name} [{referral.used_count}]",
            callback_data=f"ref-val_{referral.key}",
        )
        builder.row(button)

    await callback.message.answer("Список реферальных ссылок", reply_markup=builder.as_markup())


@menu_router.callback_query(lambda c: c.data.startswith("ref-val"))
async def ref_value_callback(callback: types.CallbackQuery):
    value = callback.data.split("_")[-1]

    await callback.message.answer(f"{BOT_START_HOST}{value}", parse_mode=ParseMode.HTML)
