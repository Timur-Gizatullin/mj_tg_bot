import datetime

import openai
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_media_group import media_group_handler
from decouple import config
from loguru import logger

from main.constants import BOT_START_HOST
from main.enums import (
    AnswerTypeEnum,
    PriceEnum,
    UserRoleEnum,
    UserStateEnum,
)
from main.handlers.helpers import is_enough_balance
from main.handlers.queue import QueueHandler
from main.handlers.utils.const import MESSAGES_URL
from main.handlers.utils.interactions import _trigger_payload, blend_trigger
from main.handlers.utils.redis.redis_mj_user import RedisMjUserTokenQueue
from main.keyboards.commands import get_commands_keyboard, resources
from main.models import (
    BanWord,
    Blend,
    Describe,
    GptContext,
    OptionPrice,
    Pay,
    Referral,
    TelegramAnswer,
    User,
)
from main.utils import (
    MenuState,
    callback_data_util,
    is_has_censor,
    put_file,
    upload_file,
)
from t_bot.settings import TELEGRAM_TOKEN

dp = Dispatcher()
bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

openai.api_key = config("OPEN_AI_API_KEY")

img_handler = {}


async def is_user_exist(chat_id: str) -> User | None:
    user = await User.objects.get_user_by_chat_id(chat_id=chat_id)
    return user


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    logger.info("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment
    amount = payment_info.total_amount // 100
    tokens = int(payment_info.invoice_payload)
    logger.info(payment_info)
    try:
        user: User = await User.objects.get_user_by_chat_id(message.chat.id)
        user.balance += tokens
        await user.asave()

        pay_dto = Pay(
            amount=amount,
            token_count=tokens,
            pay_id=payment_info.telegram_payment_charge_id,
            user=user,
            is_verified=True,
        )
        await pay_dto.asave()

        await bot.send_message(message.chat.id, f"Платеж на сумму {amount} {payment_info.currency} прошел успешно!!!")
    except Exception as e:
        logger.error(e)
        admins: list[User] = await User.objects.get_admins()
        for admin in admins:
            await bot.send_message(
                chat_id=admin.chat_id,
                text=f"Чат с номером {message.chat.id} успешно оплатитл, но из-за непредвиденной ошибки, токены не начислились, id оплаты {payment_info.telegram_payment_charge_id}",
            )


@dp.message(F.text.lower() == "gpt")
async def gpt_command(message: Message, state: FSMContext):
    answer = (
        "Введи свой запрос.\n\n"
        "Бот поддерживает функционал CHAT GPT, максимальный контекст - 15 запросов.\n\n"
        "📂Для работы с файлами, сначала вставьте ссылку в начале сообщения на файл "
        "(например  Google или Яндекс  диск) и далее укажите что с ним необходимо сделать."
    )
    await message.answer(answer)
    await state.set_state(MenuState.gpt)


@dp.message(F.text.lower() == "dall-e-3")
async def dalle_command(message: Message, state: FSMContext):
    intro_message = (
        "🌆Для создания изображения отправь боту только ключевые фразы, раздели их логической запятой;\n\n"
        "🔞Внимание!!! Строго запрещены запросы изображения 18+, работает AI модератор, несоблюдение правил приведет к бану!"
    )

    await message.answer(intro_message)
    await state.set_state(MenuState.dalle)


@dp.message(F.text.lower() == "midjourney")
async def mj_command(message: Message, state: FSMContext):
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
    await message.answer(intro_message, parse_mode=ParseMode.MARKDOWN)
    await state.set_state(MenuState.mj)


@dp.message(F.text.lower() == "личный кабинет")
async def lk_command(message: Message, state: FSMContext):
    current_user: User = await User.objects.get_user_by_chat_id(message.chat.id)
    referral: Referral = await Referral.objects.get_referral_by_user(user=current_user)
    if not referral:
        referral = await Referral.objects.create_referral(current_user)

    builder = InlineKeyboardBuilder()
    answer = f"Ваш баланс {current_user.balance}\n" f"Ваша реферальная ссылка: {BOT_START_HOST}{referral.key}"
    lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
    builder.row(*lk_buttons)
    await message.answer(answer, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)


@dp.message(CommandStart(deep_link=True))
async def deep_start(message: Message, command: CommandObject, state: FSMContext):
    key = command.args

    new_user = await is_user_exist(chat_id=str(message.chat.id))

    if new_user:
        await start_handler(message, state)
        return

    referral = await Referral.objects.get_referral(referral_key=key)

    if not referral:
        await message.answer("Ссылка не действительна")
        await start_handler(message, state)
        return

    await Referral.objects.update_referrer_generations_count(referral_key=key)

    existing_user = User(
        telegram_username=message.from_user.username, chat_id=message.chat.id, invited_by=await referral.get_referrer()
    )
    await existing_user.asave()

    await start_handler(message, state)


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    existing_user: User = await is_user_exist(chat_id=str(message.chat.id))

    username = message.from_user.username if message.from_user.username else message.from_user.id
    if not existing_user:
        existing_user = User(telegram_username=username, chat_id=message.chat.id)
        await existing_user.asave()
    elif existing_user and not existing_user.is_active:
        existing_user.is_active = True
        await existing_user.asave()

    initial_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.START)

    start_kb = await get_commands_keyboard("start", existing_user)

    await message.answer(initial_message, reply_markup=start_kb)

    kb = [
        [
            types.KeyboardButton(text="MidJourney"),
            types.KeyboardButton(text="DALL-E-3"),
        ],
        [
            types.KeyboardButton(text="GPT"),
            types.KeyboardButton(text="Личный кабинет"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, input_field_placeholder="Выберите сервис..."
    )

    await message.answer(
        f"Запуская данный бот Вы даете согласие на правила использования нашего сервиса.\n\n*Примеры генераций:* \n{resources}",
        reply_markup=keyboard,
    )


@dp.message(Command("help"))
async def help_handler(message: Message, state) -> None:
    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    help_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.HELP)

    await message.answer(help_message)


@dp.message(MenuState.mj, F.media_group_id)
@media_group_handler
async def mj_group_handler(messages: list[Message]) -> None:
    chat_id = messages[0].chat.id
    media_list = await Blend.objects.get_blends_by_group_id(messages[0].media_group_id)
    user: User = await User.objects.get_user_by_chat_id(chat_id)
    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.blend)
    if not await is_enough_balance(telegram_user=user, amount=option_price.price, message=messages[0]):
        return
    answer = await bot.send_message(chat_id, f"Загружено {len(media_list)} фотографий")
    for message in messages:
        await blend_images_handler(message)
        media_list: list[Blend] = await Blend.objects.get_blends_by_group_id(messages[0].media_group_id)
        await bot.edit_message_text(f"Загружено {len(media_list)} фотографий", chat_id, answer.message_id)
    file_names = []
    for media in media_list:
        file_name = media.uploaded_filename.split("/")[-1].split(".")[0]
        file_names.append(file_name)

    logger.debug("".join(file_names))
    new_blend = Blend(
        user=user, group_id=media_list[0].group_id, uploaded_filename="".join(file_names), chat_id=messages[0].chat.id
    )
    await new_blend.asave()
    await blend_trigger(media_list, answer, user)


@dp.message(MenuState.mj)
async def mj_handler(message: Message) -> None:
    user = await is_user_exist(chat_id=str(message.chat.id))

    if not user:
        await message.answer("Напишите боту /start")
        return

    if user.state == UserStateEnum.PENDING:
        await message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        return
    if user.state == UserStateEnum.BANNED:
        await message.answer("🛑 Ваш аккаунт был ограничен, обратитесь к администратору")
        return

    if message.text and not message.photo and not message.media_group_id:
        await handle_imagine(message)
    elif message.photo and not message.text and not message.media_group_id and not message.caption:
        await describe_handler(message)
    elif message.photo and message.caption and not message.media_group_id:
        await based_on_photo_imagine(message=message, user=user)


@dp.message(MenuState.gpt)
async def gpt_handler(message: types.Message):
    user = await is_user_exist(chat_id=str(message.chat.id))
    if not user:
        await message.answer("Напишите боту /start")
        return

    if user.state == UserStateEnum.PENDING:
        await message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        return
    if user.state == UserStateEnum.BANNED:
        await message.answer("🛑 Ваш аккаунт был ограничен, обратитесь к администратору")
        return

    user.state = UserStateEnum.PENDING
    user.pending_state_at = datetime.datetime.now()
    await user.asave()

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message.text and not await is_has_censor(message.text, ban_words):
        await message.answer(censor_message_answer)
        return

    new_gpt_context = GptContext(user=user, role="user", content=message.text, telegram_chat_id=message.chat.id)
    await new_gpt_context.asave()

    gpt_contexts: list[GptContext] = await GptContext.objects.get_gpt_contexts_by_telegram_chat_id(
        telegram_chat_id=message.chat.id
    )
    messages = []
    for gpt_context in gpt_contexts:
        gpt_message = {"role": gpt_context.role, "content": gpt_context.content}
        messages.append(gpt_message)

    try:
        answer = await message.answer("GPT думает ...")
        gpt_answer = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=messages)
    except Exception as e:
        logger.error(f"Не удалось получить ответ от ChatGPT из-за непредвиденной ошибки\n{e}")
        user.state = UserStateEnum.READY
        await user.asave()
        await message.answer("ChatGPT временно не доступен, попробуйте позже")
        return

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="сбросить контекст", callback_data="gpt"))

    await answer.edit_text(gpt_answer.choices[0].message.content, reply_markup=builder.as_markup())

    user.state = UserStateEnum.READY

    if len(gpt_contexts) >= 15:
        await GptContext.objects.delete_gpt_contexts(gpt_contexts)
        await message.answer("Контекст очищен")

    option_price: OptionPrice = await OptionPrice.objects.get_price_by_product(PriceEnum.gpt)
    user.balance -= option_price.price
    if user.balance <= 5 and user.role != UserRoleEnum.ADMIN:
        user.role = UserRoleEnum.BASE
    await user.asave()
    await message.answer(text=f"Баланс в токенах {user.balance}")


@dp.message(MenuState.dalle)
async def dale_handler(message: Message):
    user = await is_user_exist(chat_id=str(message.chat.id))
    suggestion = await TelegramAnswer.objects.get_message_by_type(AnswerTypeEnum.GPT_PRICE)
    callback_data_util[f"{message.chat.id}-{message.message_id}"] = message.text
    builder = InlineKeyboardBuilder()
    prompt_buttons = (
        types.InlineKeyboardButton(
            text="CHAT GPT", callback_data=f"dalle_suggestion_gpt_{message.chat.id}-{message.message_id}"
        ),
        types.InlineKeyboardButton(
            text="Оставить мой", callback_data=f"dalle_suggestion_stay_{message.chat.id}-{message.message_id}"
        ),
    )
    kb = builder.row(*prompt_buttons)
    await message.answer(suggestion, reply_markup=kb.as_markup())


async def handle_imagine(message, img_url: str | None = None):
    if message.text and "\n" in message.text:
        await message.answer("⛔️Промт должен содержать только одну строку⛔️")
        return

    if message.caption and "\n" in message.caption:
        await message.answer("⛔️Промт должен содержать только одну строку⛔️")
        return

    suggestion = await TelegramAnswer.objects.get_message_by_type(AnswerTypeEnum.GPT_PRICE)
    text = message.caption if img_url else message.text
    callback_data_util[f"{message.chat.id}-{message.message_id}"] = {"text": text, "img": img_url}
    builder = InlineKeyboardBuilder()
    prompt_buttons = (
        types.InlineKeyboardButton(
            text="CHAT GPT", callback_data=f"suggestion_gpt_{message.chat.id}-{message.message_id}"
        ),
        types.InlineKeyboardButton(
            text="Оставить мой", callback_data=f"suggestion_stay_{message.chat.id}-{message.message_id}"
        ),
    )
    kb = builder.row(*prompt_buttons)
    await message.answer(suggestion, reply_markup=kb.as_markup())


async def blend_images_handler(message: Message):
    user = await is_user_exist(chat_id=str(message.chat.id))
    if not user:
        await message.answer("Напишите боту /start")
        user.state = UserStateEnum.PENDING
        user.pending_state_at = datetime.datetime.now()
        await user.asave()
        return

    file = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_path=file.file_path)
    token = await RedisMjUserTokenQueue().get_sender_token(user)
    header = {"authorization": token, "Content-Type": "application/json"}

    attachment = await upload_file(file=file, header=header, chat_id=message.chat.id)
    if not attachment:
        await message.answer("Не удалось загрузить файлы")
        return

    if not (await put_file(downloaded_file=downloaded_file, attachment=attachment)).ok:
        await message.answer("Не удалось загрузить файлы")
        return

    upload_filename = attachment["upload_filename"]

    new_blend = Blend(
        user=user,
        group_id=message.media_group_id,
        uploaded_filename=upload_filename,
    )

    await new_blend.asave()


async def based_on_photo_imagine(message: Message, user):
    file = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_path=file.file_path)
    token = await RedisMjUserTokenQueue().get_sender_token(user)
    header = {"authorization": token, "Content-Type": "application/json"}

    attachment = await upload_file(file=file, header=header, chat_id=message.chat.id)
    if not attachment:
        await message.answer("Не удалось загрузить файлы")
        return

    if not (await put_file(downloaded_file=downloaded_file, attachment=attachment)).ok:
        await message.answer("Не удалось загрузить файлы")
        return

    upload_filename = attachment["upload_filename"].split("/")[-1]
    logger.debug(attachment)
    logger.debug(upload_filename)

    header = {"authorization": token, "Content-Type": "application/json"}
    payload = {
        "content": "",
        "channel_id": "1160854221990662146",
        "type": 0,
        "sticker_ids": [],
        "attachments": [
            {
                "id": "0",
                "filename": upload_filename,
                "uploaded_filename": attachment["upload_filename"],
            }
        ],
    }

    image_data = requests.post(url=MESSAGES_URL, json=payload, headers=header)

    if image_data.ok:
        image_data = image_data.json()
        logger.error(image_data)
    else:
        logger.error(image_data.text)
        await message.answer("Не удалось загрузить фото")
        return

    img_url = image_data["attachments"][0]["proxy_url"]

    await handle_imagine(message=message, img_url=img_url)


async def describe_handler(message: Message):
    user = await is_user_exist(str(message.chat.id))
    if not user:
        await message.answer("Напишите /start")
        return
    option_price = await OptionPrice.objects.get_price_by_product(PriceEnum.describe)
    await is_enough_balance(telegram_user=user, amount=option_price.price, message=message)
    if user.state == UserStateEnum.PENDING:
        await message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        return
    if user.state == UserStateEnum.BANNED:
        await message.answer("🛑 Ваш аккаунт был ограничен, обратитесь к администратору")
        return

    file = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_path=file.file_path)
    token = await RedisMjUserTokenQueue().get_sender_token(user)
    header = {"authorization": token, "Content-Type": "application/json"}

    attachment = await upload_file(file=file, header=header, chat_id=message.chat.id)
    if not attachment:
        await message.answer("Не удалось загрузить файл")
        user.state = UserStateEnum.READY
        await user.asave()
        return

    if not (await put_file(downloaded_file=downloaded_file, attachment=attachment)).ok:
        await message.answer("Не удалось загрузить файл")
        user.state = UserStateEnum.READY
        await user.asave()
        return

    upload_filename = attachment["upload_filename"]

    payload = _trigger_payload(
        2,
        {
            "version": "1166847114203123797",
            "id": "1092492867185950852",
            "name": "describe",
            "type": 1,
            "options": [{"type": 11, "name": "image", "value": 0}],
            "attachments": [
                {
                    "id": "0",
                    "filename": upload_filename.split("/")[-1],
                    "uploaded_filename": upload_filename,
                }
            ],
        },
    )

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="describe")

    new_describe = Describe(file_name=upload_filename.split("/")[-1], chat_id=str(message.chat.id))
    await new_describe.asave()


@dp.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message()
async def handle_any(message: Message, state):
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    await help_handler(message, state)
