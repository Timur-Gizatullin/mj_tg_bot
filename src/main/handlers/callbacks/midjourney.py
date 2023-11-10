import datetime
import os

import django
from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.enums import AnswerTypeEnum, UserStateEnum, PriceEnum
from main.handlers.commands import bot
from main.handlers.helpers import (
    get_gpt_prompt_suggestions,
    gpt_translate,
    is_can_use,
    is_enough_balance,
    is_ready,
)
from main.handlers.utils.interactions import (
    imagine_trigger,
    send_pan_trigger,
    send_reset_trigger,
    send_upsample_trigger,
    send_variation_trigger,
    send_vary_trigger,
    send_zoom_trigger, describe_reset_trigger,
)
from main.utils import callback_data_util, is_has_censor

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import BanWord, Prompt, TelegramAnswer, User, OptionPrice  # noqa: E402

mj_router = Router()

help_message = (
    "🪄Vary Strong - вносит больше изменений в создаваемые вариации, увеличивает урвоень художественности и "
    "воображемых элементов\n\n"
    "🪄Vary stable - вносит небольшие изменения в создоваемые вариации, приближает изображение к стандартным \n\n"
    "🔍Zoom out - масштабирует сгенерированную картинку,  дорисовывая объект и фон\n\n"
    "🔼Upscale -  увеличивает размер изображения, добавляя мельчайшие детали,"
    " в 2 (2048х2048) и 4 рааза (4096х4096), стандартное изображение - 1024x1024.\n\n"
    "⬅️⬆️⬇️➡️ расширяет изображение в указанную сторону, дорисовывая объект и фон"
)


@mj_router.callback_query(lambda c: c.data.startswith("V"))
async def callbacks_variations(callback: types.CallbackQuery):
    action = callback.data
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user: User = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.variation)
    if not await is_enough_balance(telegram_user=telegram_user, callback=callback, amount=option_price.price):
        return
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    if action == "V1":
        await send_variation_trigger(variation_index="1", queue=queue, message=callback.message, user=telegram_user)
    elif action == "V2":
        await send_variation_trigger(variation_index="2", queue=queue, message=callback.message, user=telegram_user)
    elif action == "V3":
        await send_variation_trigger(variation_index="3", queue=queue, message=callback.message, user=telegram_user)
    elif action == "V4":
        await send_variation_trigger(variation_index="4", queue=queue, message=callback.message, user=telegram_user)

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("_v5"))
async def callbacks_upsamples_v5(callback: types.CallbackQuery):
    action = callback.data
    cancel = callback.data.split("_")[-1]
    message_hash = callback.message.document.file_name.split(".")[0]
    logger.debug(action)
    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.upscale__v5_2x) if action == "2x" else await OptionPrice.objects.get_price_by_product(PriceEnum.upscale__v5_4x)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    await send_upsample_trigger(
        upsample_index="1", queue=queue, version=action, message=callback.message, user=telegram_user
    )

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("confirm_v5"))
async def callbacks_confirm_upsamples_v5(callback: types.CallbackQuery):
    action = callback.data.split("_")[-1]
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="ДА!", callback_data=f"_v5_{action}"),
    )
    await bot.send_document(
        chat_id=callback.message.chat.id,
        caption=await TelegramAnswer.objects.get_message_by_type(AnswerTypeEnum.UPSCALE_CONFIRM),
        reply_markup=builder.as_markup(),
        document=callback.message.document.file_id,
    )
    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("U"))
async def callbacks_upsamples(callback: types.CallbackQuery):
    action = callback.data
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)
    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.upsample)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    await callback.message.answer(help_message)

    if action == "U1":
        await send_upsample_trigger(upsample_index="1", queue=queue, message=callback.message, user=telegram_user)
    elif action == "U2":
        await send_upsample_trigger(upsample_index="2", queue=queue, message=callback.message, user=telegram_user)
    elif action == "U3":
        await send_upsample_trigger(upsample_index="3", queue=queue, message=callback.message, user=telegram_user)
    elif action == "U4":
        await send_upsample_trigger(upsample_index="4", queue=queue, message=callback.message, user=telegram_user)

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("vary"))
async def callback_vary(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.vary)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    if action == "strong":
        await send_vary_trigger(vary_type="high_variation", queue=queue, message=callback.message, user=telegram_user)
    elif action == "subtle":
        await send_vary_trigger(vary_type="low_variation", queue=queue, message=callback.message, user=telegram_user)

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("reset"))
async def callback_reset(callback: types.CallbackQuery):
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.reroll)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    await send_reset_trigger(
        message_id=queue.discord_message_id,
        message_hash=queue.message_hash,
        message=callback.message,
        user=telegram_user,
    )

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("zoom"))
async def callback_zoom(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.zoom)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    if action == "2":
        await send_zoom_trigger(queue=queue, zoomout="1", message=callback.message, user=telegram_user)
    elif action == "1.5":
        await send_zoom_trigger(queue=queue, zoomout=action, message=callback.message, user=telegram_user)

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("pan"))
async def callback_pan(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.pan)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    await send_pan_trigger(queue=queue, direction=action, message=callback.message, user=telegram_user)

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("suggestion"))
async def suggestion_callback(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_id = callback.data.split("_")[-1]
    data = callback_data_util.get(message_id, None)
    logger.debug(data)
    if not data:
        await callback.message.answer("Сообщение удалено из кэша, введите ваш промпт снова")
        await callback.answer()
        return
    message = data.get("text", None)
    if not message:
        await callback.message.answer("Сообщение удалено из кэша, введите ваш промпт снова")
        await callback.answer()
        return
    user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if not await is_ready(user, callback):
        return
    user.state = UserStateEnum.PENDING
    user.pending_state_at = datetime.datetime.now()
    await user.asave()

    prompt = await gpt_translate(message)

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)
    logger.debug(prompt)
    if message and not await is_has_censor(prompt, ban_words):
        await callback.message.answer(censor_message_answer)
        user.state = UserStateEnum.READY
        await user.asave()
        return

    if action == "gpt":
        option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.gpt)
        if not await is_enough_balance(telegram_user=user, callback=callback, amount=option_price.price):
            return
        await get_gpt_prompt_suggestions(prompt, callback, user, data)
        return
    if action == "stay":
        option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.imagine)
        if not await is_enough_balance(telegram_user=user, callback=callback, amount=option_price.price):
            return

        if data["img"]:
            prompt = f"{data['img']} {prompt}"

        await imagine_trigger(callback.message, prompt, user=user)


@mj_router.callback_query(lambda c: c.data.startswith("choose-gpt"))
async def gpt_choose_callback(callback: types.CallbackQuery):
    choose = int(callback.data.split("_")[1])
    img_id = f"img{callback.data.split('_')[-1]}"
    logger.debug(img_id)
    telegram_user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.imagine)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    try:
        prompt = callback.message.text.split("\n\n")[choose - 1][2:]
    except Exception:
        prompt = callback.message.text.split("\n")[choose - 1][2:]

    prompt = prompt if prompt[-1] != "." else prompt[:-1]

    img_url = callback_data_util.get(img_id, None)

    prompt = f"{img_url} {prompt}" if img_url else prompt

    await imagine_trigger(message=callback.message, prompt=prompt, user=telegram_user)

    await callback.answer()


@mj_router.callback_query(lambda c: c.data.startswith("describe"))
async def callbacks_describe(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    telegram_user: User = await User.objects.get_user_by_chat_id(chat_id=callback.message.chat.id)

    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.describe)
    if not await is_can_use(telegram_user, callback, option_price.price):
        return

    if callback.data != "reset" and action != "all":
        prompt = callback.message.caption.split("\n\n")[int(action)]
        logger.debug(callback.message.caption)
        logger.debug(prompt)

        await imagine_trigger(message=callback.message, prompt=prompt, user=telegram_user)
    elif callback.data == "reset":
        await describe_reset_trigger(message_id=telegram_user.chat_id, message=callback.message, user=telegram_user)

    await callback.answer()
