import os

import django
import langdetect
import openai
import requests
from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.constants import BOT_HOST
from main.enums import AnswerTypeEnum, UserRoleEnum, UserStateEnum
from main.handlers.commands import bot, gpt, is_user_exist
from main.handlers.utils.interactions import (
    blend_trigger,
    describe_reset_trigger,
    imagine_trigger,
    send_pan_trigger,
    send_reset_trigger,
    send_upsample_trigger,
    send_variation_trigger,
    send_vary_trigger,
    send_zoom_trigger,
)
from main.handlers.utils.wallet import get_pay_link
from main.keyboards.commands import resources
from main.keyboards.pay import get_inline_keyboard_from_buttons
from main.utils import MenuState, callback_data_util, is_has_censor

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import (  # noqa: E402
    BanWord,
    Blend,
    GptContext,
    Prompt,
    Referral,
    TelegramAnswer,
    User,
)

callback_router = Router()
GPT_OPTION = """The ethereal quality of the charcoal brings a nostalgic feel that complements the natural light streaming softly through a lace-curtained window. In the background, the texture of the vintage furniture provides an intricate carpet of detail, with a monochromatic palette serving to emphasize the subject of the piece. This charcoal drawing imparts a sense of tranquillity and wisdom with an authenticity that captures the subject's essence. Use different lenses, cameras, focus, light and scenes options. 
 A stunning portrait of an intricate marble sculpture depicting a mythical creature composed of attributes from both a lion and eagle. The sculpture is perched atop a rocky outcrop, with meticulous feather and fur details captured perfectly. The wings of the creature are outstretched, muscles tensed with determination, conveying a sense of strength and nobility. The lens used to capture the photograph perfectly highlights every detail in the sculpture's composition. The image has a sharp focus and excellent clarity. Canon EF 24-70mm f/2.8L II USM lens at 50mm, ISO 100, f/5.6, 1/50s, --ar 4:3

 Astounding astrophotography image of the Milky Way over Stonehenge, emphasizing the human connection to the cosmos across time. The enigmatic stone structure stands in stark silhouette with the awe-inspiring night sky, showcasing the complexity and beauty of our galaxy. The contrast accentuates the weathered surfaces of the stones, highlighting their intricate play of light and shadow. Sigma Art 14mm f/1.8, ISO 3200, f/1.8, 15s --ar 16:9

 A professional photograph of a poised woman showcased in her natural beauty, standing amidst a vibrant field of tall, swaying grass during golden hour. The radiant rays of sun shimmer and cast a glow around her. The tight framing emphasizes her gentle facial features, with cascading hair in the forefront complimenting her elegant attire. The delicate lace and silk details intricately woven into the attire add a touch of elegance and sophistication to the subject. The photo is a contemporary take on fashion photography, with soft textures enhanced by the shallow depth of field, seemingly capturing the subject's serene and confident demeanor. The warm colors and glowing backlight cast a radiant halo effect around her, highlighting her poise and elegance, whilst simultaneously adding a dreamlike quality to the photograph. Otus 85mm f/1.4 ZF.2 Lens, ISO 200, f/4, 1/250s --ar 2:3

use different lens and cameras

You will now receive a text prompt from me and then create three creative prompts for the Midjourney AI art generator using the best practices mentioned above. Do not include explanations in your response. List three prompts with correct syntax without unnecessary words. Do not generate any prompts until I give you specific input to do so. Use different code blocks for every single text prompt, to make it easy to copy.
Yoy always give 3 options.
"""


@callback_router.callback_query(lambda c: c.data.startswith("V"))
async def callbacks_variations(callback: types.CallbackQuery):
    action = callback.data
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user: User = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING
    await telegram_user.asave()

    if action == "V1":
        await send_variation_trigger(variation_index="1", queue=queue, message=callback.message)
    elif action == "V2":
        await send_variation_trigger(variation_index="2", queue=queue, message=callback.message)
    elif action == "V3":
        await send_variation_trigger(variation_index="3", queue=queue, message=callback.message)
    elif action == "V4":
        await send_variation_trigger(variation_index="4", queue=queue, message=callback.message)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("confirm_v5"))
async def callbacks_confirm_upsamples_v5(callback: types.CallbackQuery):
    action = callback.data.split("_")[-1]
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="ДА!", callback_data=f"_v5_{action}"),
        types.InlineKeyboardButton(text="НЕТ!", callback_data="_v5_cancel"),
    )
    await bot.send_document(
        chat_id=callback.message.chat.id,
        caption="Upscale -  увеличивает размер изображения, добавляя мельчайшие детали, в 2 (2048х2048) "
        "и 4 раза (4096х4096), файлы 4х  могут не открываться на смартфоне, используйте компьютер.\n"
        "Стоимость:\n"
        "Upscale 2x = 4 токена\n"
        "Upscale 4x = 8 токенов\n\n"
        "Сгенерировать?",
        reply_markup=builder.as_markup(),
        document=callback.message.document.file_id,
    )
    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("_v5"))
async def callbacks_upsamples_v5(callback: types.CallbackQuery):
    action = callback.data
    cancel = callback.data.split("_")[-1]
    message_hash = callback.message.document.file_name.split(".")[0]
    logger.debug(action)
    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if cancel == "cancel":
        await callback.message.answer("Отменено")
        telegram_user.state = UserStateEnum.READY
        await telegram_user.asave()
        return

    if action == "2x":
        cost = 4
    else:
        cost = 8

    if telegram_user.balance - cost < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING

    await send_upsample_trigger(upsample_index="1", queue=queue, version=action, message=callback.message)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("U"))
async def callbacks_upsamples(callback: types.CallbackQuery):
    action = callback.data
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING

    help_message = (
        "🪄Vary Strong - вносит больше изменений в создаваемые вариации, увеличивает урвоень художественности и "
        "воображемых элементов\n\n"
        "🪄Vary stable - вносит небольшие изменения в создоваемые вариации, приближает изображение к стандартным \n\n"
        "🔍Zoom out - масштабирует сгенерированную картинку,  дорисовывая объект и фон\n\n"
        "🔼Upscale -  увеличивает размер изображения, добавляя мельчайшие детали,"
        " в 2 (2048х2048) и 4 рааза (4096х4096), стандартное изображение - 1024x1024.\n\n"
        "⬅️⬆️⬇️➡️ расширяет изображение в указанную сторону, дорисовывая объект и фон"
    )

    await callback.message.answer(help_message)

    if action == "U1":
        await send_upsample_trigger(upsample_index="1", queue=queue, message=callback.message)
    elif action == "U2":
        await send_upsample_trigger(upsample_index="2", queue=queue, message=callback.message)
    elif action == "U3":
        await send_upsample_trigger(upsample_index="3", queue=queue, message=callback.message)
    elif action == "U4":
        await send_upsample_trigger(upsample_index="4", queue=queue, message=callback.message)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("reset"))
async def callback_reset(callback: types.CallbackQuery):
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING

    await send_reset_trigger(
        message_id=queue.discord_message_id, message_hash=queue.message_hash, message=callback.message
    )

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("vary"))
async def callback_vary(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING
    await telegram_user.asave()

    if action == "strong":
        await send_vary_trigger(vary_type="high_variation", queue=queue, message=callback.message)
    elif action == "subtle":
        await send_vary_trigger(vary_type="low_variation", queue=queue, message=callback.message)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("zoom"))
async def callback_zoom(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING

    if action == "2":
        await send_zoom_trigger(queue=queue, zoomout=1, message=callback.message)
    elif action == "1.5":
        await send_zoom_trigger(queue=queue, zoomout=action, message=callback.message)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("pan"))
async def callback_pan(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_hash = callback.message.document.file_name.split(".")[0]

    queue: Prompt = await Prompt.objects.get_prompt_by_message_hash(message_hash=message_hash)
    telegram_user = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING

    await send_pan_trigger(queue=queue, direction=action, message=callback.message)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("pay_choose"))
async def callback_pay(callback: types.CallbackQuery):
    action = callback.data.split("_")[-3]
    amount = callback.data.split("_")[-2]
    token = callback.data.split("_")[-1]

    amount = str(float(int(amount) // 100))
    logger.debug(action)
    if action == "wallet":
        desc = "Get tokens for Mid Journey telegram bot"

        pay_link = await get_pay_link(
            amount=amount,
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
        key_board = get_inline_keyboard_from_buttons((pay_button,))

        await callback.message.answer(f"Get {token} tokens for {amount}$", reply_markup=key_board)
        await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("describe"))
async def callbacks_describe(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    telegram_user: User = await User.objects.get_user_by_chat_id(chat_id=callback.message.chat.id)

    if telegram_user.balance < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING

    if callback.data != "reset" and action != "all":
        prompt = callback.message.caption.split("\n\n")[int(action)]
        logger.debug(callback.message.caption)
        logger.debug(prompt)

        await imagine_trigger(message=callback.message, prompt=prompt)
    elif callback.data == "reset":
        await describe_reset_trigger(message_id=telegram_user.chat_id, message=callback.message)

    await callback.answer()


# Common


@callback_router.callback_query(lambda c: c.data.startswith("start"))
async def menu_start_callback(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    current_user: User = await User.objects.get_user_by_chat_id(str(callback.message.chat.id))

    if action == "mj":
        intro_message = (
            "🌆Для создания изображения отправь боту только ключевые фразы, раздели их логической запятой;\nНапример:\n"
            "`Бред Пит в роли Терминатор сидит на мотоцикле, огонь на заднем плане`\n\n"
            "❗Порядок слов очень важен! Чем раньше слово, тем сильнее его вес;\n"
            "🛑 Не нужно писать  “создай изображение”, это ухудшит результат;\n\n"
            "📌Для создания изображения на основании твоего или объединения двух изображений, отправь картинку боту и напиши промпт в комментарии к ней;\n\n"
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
            "Введи свой запрос с командой /gpt\n\n"
            "Бот поддерживает функционал CHAT GPT4, максимальный контекст - 15 запросов.\n\n"
            "📂Для работы с файлами, просто отправьте файл боту для его обработки и "
            "укажите что с ним необходимо сделать в комментарии"
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
        answer = f"Ваш баланс {current_user.balance}\n" f"Ваша реферальная ссылка: {BOT_HOST}{referral.key}"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())

        await callback.answer()
        return
    if action == "ref":
        referral: Referral = await Referral.objects.get_referral_by_user(user=current_user)
        if not referral:
            referral = await Referral.objects.create_referral(current_user)

        answer = (
            "За каждого реферала Вам будет начислено 6 токенов\n\n" f"Ваша реферальная ссылка: {BOT_HOST}{referral.key}"
        )
        await callback.message.answer(answer)

        await callback.answer()
        return


@callback_router.callback_query(lambda c: c.data.startswith("lk"))
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
            "Одна генерация Dal-E = 2\n"
            "Один запрос Chat GPT в т.ч. По формированию промпта = 1\n"
            "При оплате в USDT - 1 usdt = 100р"
        )

        options_button = (
            types.InlineKeyboardButton(text="4 токена = 20 руб", callback_data="pay-options_4_20"),
            types.InlineKeyboardButton(text="10 токенов = 50 руб", callback_data="pay-options_10_50"),
            types.InlineKeyboardButton(text="20 токенов = 90 руб", callback_data="pay-options_20_90"),
            types.InlineKeyboardButton(text="50 токенов = 200 руб", callback_data="pay-options_50_200"),
            types.InlineKeyboardButton(text="100 токенов = 400 руб", callback_data="pay-options_100_400"),
            types.InlineKeyboardButton(text="200 токенов = 800 руб", callback_data="pay-options_200_800"),
            types.InlineKeyboardButton(text="400 токенов = 1500 руб", callback_data="pay-options_400_1500"),
            types.InlineKeyboardButton(text="1000 токенов = 3000 руб", callback_data="pay-options_1000_3000"),
        )

        builder = InlineKeyboardBuilder()
        j = 0
        for i in range(len(options_button) // 2):
            builder.row(options_button[j], options_button[j + 1])
            j += 2

        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("pay-options"))
async def pay_options_callback(callback: types.CallbackQuery):
    token = callback.data.split("_")[1]
    amount = callback.data.split("_")[-1]

    answer = f"Платеж на {token} успешно создан"
    builder = InlineKeyboardBuilder()
    buttons = (
        # types.InlineKeyboardButton(
        #     text="Любой картой РФ (Юкасса)", callback_data=f"pay_choose_yokasa_{amount}_{token}"
        # ),
        types.InlineKeyboardButton(text="Telegram Wallet", callback_data=f"pay_choose_wallet_{amount}_{token}"),
    )
    for button in buttons:
        builder.row(button)

    await callback.message.answer(answer, reply_markup=builder.as_markup())
    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("suggestion"))
async def suggestion_callback(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    message_id = callback.data.split("_")[-1]
    message = callback_data_util.get(message_id)
    if not message:
        await callback.message.answer("Сообщение удалено из кэша, введите ваш промпт снова")
        await callback.answer()
        return
    user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    locale = langdetect.detect(message)
    if locale == "en":
        prompt = message
    else:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional translator from Russian into English, "
                    "everything that is said to you, you translate into English"
                ),
            },
            {"role": "user", "content": message},
        ]

        prompt = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)
        prompt = prompt.choices[0].message.content

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message and await is_has_censor(prompt, ban_words):
        await callback.message.answer(censor_message_answer)
        user.state = UserStateEnum.READY
        await user.asave()
        return

    user.state = UserStateEnum.PENDING
    await user.asave()

    if action == "gpt":
        if user.balance - 1 < 0:
            builder = InlineKeyboardBuilder()
            answer = f"Ваш баланс {user.balance}\n"
            lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
            builder.row(*lk_buttons)
            await callback.message.answer(answer, reply_markup=builder.as_markup())
            await callback.answer()
            return

        messages = [
            {"role": "system", "content": GPT_OPTION},
            {"role": "user", "content": prompt},
        ]
        await callback.message.answer(f"GPT думает ... ⌛\n")
        prompt_suggestions = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)

        builder = InlineKeyboardBuilder()
        buttons = [types.InlineKeyboardButton(text=f"промпт {i}", callback_data=f"choose-gpt_{i}") for i in range(1, 4)]
        builder.row(*buttons)

        user.balance -= 1
        if user.balance < 5:
            user.role = UserRoleEnum.BASE
        user.state = UserStateEnum.READY
        await user.asave()

        await callback.message.answer(
            text=prompt_suggestions.choices[0].message.content, reply_markup=builder.as_markup()
        )
        await callback.message.answer(text=f"Баланс в токенах: {user.balance}")
        await callback.answer(cache_time=4000)
        return
    if action == "stay":
        if user.balance - 2 < 0:
            builder = InlineKeyboardBuilder()
            answer = f"Ваш баланс {user.balance}\n"
            lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
            builder.row(*lk_buttons)
            await callback.message.answer(answer, reply_markup=builder.as_markup())
            await callback.answer()
            user.state = UserStateEnum.READY
            await user.asave()

        await imagine_trigger(callback.message, prompt)
        await callback.answer(cache_time=2000)


@callback_router.callback_query(lambda c: c.data.startswith("dalle"))
async def dalle_suggestion_callback(callback: types.CallbackQuery):
    action = callback.data.split("_")[2]
    message_id = callback.data.split("_")[-1]
    message = callback_data_util.get(message_id)
    if not message:
        await callback.message.answer("Сообщение удалено из кэша, введите ваш промпт снова")
        await callback.answer()
        return
    user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    locale = langdetect.detect(message)
    if locale == "en":
        prompt = message
    else:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional translator from Russian into English, "
                    "everything that is said to you, you translate into English"
                ),
            },
            {"role": "user", "content": message},
        ]

        answer = await callback.message.answer(f"GPT думает ... ⌛\n")
        prompt = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)
        prompt = prompt.choices[0].message.content

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message and await is_has_censor(prompt, ban_words):
        await callback.message.answer(censor_message_answer)
        user.state = UserStateEnum.READY
        await user.asave()
        return

    user.state = UserStateEnum.PENDING
    await user.asave()

    if action == "gpt":
        if user.balance - 1 < 0:
            builder = InlineKeyboardBuilder()
            answer = f"Ваш баланс {user.balance}\n"
            lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
            builder.row(*lk_buttons)
            await callback.message.answer(answer, reply_markup=builder.as_markup())
            await callback.answer()
            return

        messages = [
            {"role": "system", "content": GPT_OPTION},
            {"role": "user", "content": prompt},
        ]
        answer = await callback.message.answer(f"GPT думает ... ⌛\n")
        prompt_suggestions = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)

        builder = InlineKeyboardBuilder()
        buttons = [
            types.InlineKeyboardButton(text=f"промпт {i}", callback_data=f"choose-dalle-gpt_{i}") for i in range(1, 4)
        ]
        builder.row(*buttons)

        user.balance -= 1
        if user.balance < 5:
            user.role = UserRoleEnum.BASE
        user.state = UserStateEnum.READY
        await user.asave()

        await answer.edit_text(text=prompt_suggestions.choices[0].message.content, reply_markup=builder.as_markup())
        await callback.message.answer(text=f"Ваш баланс в токенах: {user.balance}")
        await callback.answer(cache_time=100)
        return
    if action == "stay":
        if user.balance - 2 < 0:
            builder = InlineKeyboardBuilder()
            answer = f"Ваш баланс {user.balance}\n"
            lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
            builder.row(*lk_buttons)
            await callback.message.answer(answer, reply_markup=builder.as_markup())
            await callback.answer()
            return

        await callback.message.answer("Идет генирация... ⌛\n")
        img_data = await openai.Image.acreate(prompt=prompt, n=1, size="1024x1024")
        img_links = img_data["data"]
        for img_link in img_links:
            raw_image = requests.get(img_link["url"]).content
            img = BufferedInputFile(file=raw_image, filename=f"{callback.message.message_id}.png")
            await bot.send_photo(
                chat_id=callback.message.chat.id, photo=img, caption=f"`{prompt}`", parse_mode=ParseMode.MARKDOWN
            )

        user.balance -= 2
        if user.balance < 5:
            user.role = UserRoleEnum.BASE
        user.state = UserStateEnum.READY
        await user.asave()

        await bot.send_message(chat_id=callback.message.chat.id, text=f"Баланс в токенах {user.balance}\n\n{resources}")

        await callback.answer(cache_time=60)
        return


@callback_router.callback_query(lambda c: c.data.startswith("gpt"))
async def gpt_callback(callback: types.CallbackQuery):
    gpt_contexts = await GptContext.objects.get_gpt_contexts_by_telegram_chat_id(callback.message.chat.id)
    await GptContext.objects.delete_gpt_contexts(gpt_contexts)

    await callback.answer("Контекст очищен")


@callback_router.callback_query(lambda c: c.data.startswith("choose-gpt"))
async def gpt_choose_callback(callback: types.CallbackQuery):
    choose = int(callback.data.split("_")[1])
    telegram_user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING
    await telegram_user.asave()

    try:
        prompt = callback.message.text.split("\n\n")[choose - 1][2:]
    except Exception:
        prompt = callback.message.text.split("\n")[choose - 1][2:]

    await imagine_trigger(message=callback.message, prompt=prompt)

    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("choose-dalle-gpt"))
async def gpt_dalle_choose_callback(callback: types.CallbackQuery):
    choose = int(callback.data.split("_")[1])
    telegram_user: User = await User.objects.get_user_by_chat_id(callback.message.chat.id)

    if telegram_user.balance - 2 < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return

    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return

    telegram_user.state = UserStateEnum.PENDING
    await telegram_user.asave()

    try:
        prompt = callback.message.text.split("\n\n")[choose - 1][2:]
    except Exception:
        prompt = callback.message.text.split("\n")[choose - 1][2:]

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

    await callback.answer(cache_time=500)


@callback_router.callback_query(lambda c: c.data.startswith("blend"))
async def blend_callback(callback: types.CallbackQuery):
    action = callback.data.split("_")[-1]
    user = await is_user_exist(chat_id=str(callback.message.chat.id))
    if not user:
        await callback.message.answer("Напишите боту /start")
        return

    blends = await Blend.objects.get_blends_by_group_id(action)

    response = await blend_trigger(blends)
    logger.debug(response.text)

    user.state = UserStateEnum.READY
    await user.asave()
