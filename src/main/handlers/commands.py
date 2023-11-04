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

from main.enums import AnswerTypeEnum, UserRoleEnum, UserStateEnum
from main.handlers.queue import QueueHandler
from main.handlers.utils.const import MESSAGES_URL
from main.handlers.utils.interactions import (
    _trigger_payload,
    blend_trigger,
    mj_user_token_queue,
)
from main.keyboards.commands import get_commands_keyboard, resources
from main.models import (
    BanWord,
    Blend,
    Describe,
    GptContext,
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
gpt = openai.ChatCompletion

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

    await start_handler(message, state)


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    existing_user: User = await is_user_exist(chat_id=str(message.chat.id))

    username = message.from_user.username if message.from_user.username else message.from_user.id
    if not existing_user:
        user = User(telegram_username=username, chat_id=message.chat.id)
        await user.asave()

    initial_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.START)

    start_kb = await get_commands_keyboard("start")

    await message.answer(initial_message, reply_markup=start_kb)

    await message.answer(
        f"Запуская данный бот Вы даете согласие на правила использования нашего сервиса.\n\n{resources}"
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
    await blend_trigger(media_list, answer)


@dp.message(MenuState.mj)
async def mj_handler(message: Message) -> None:
    user = await is_user_exist(chat_id=str(message.chat.id))

    if not user:
        await message.answer("Напишите боту /start")
        return

    if user.state == UserStateEnum.PENDING:
        await message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        return

    user.state = UserStateEnum.PENDING
    await user.asave()
    logger.debug(message.media_group_id)
    if message.text and not message.photo and not message.media_group_id:
        await handle_imagine(message)
    elif message.photo and not message.text and not message.media_group_id and not message.caption:
        await describe_handler(message, user)
    elif message.photo and message.caption and not message.media_group_id:
        await based_on_photo_imagine(message=message)


@dp.message(MenuState.gpt)
async def gpt_handler(message: types.Message):
    user = await is_user_exist(chat_id=str(message.chat.id))
    if not user:
        await message.answer("Напишите боту /start")
        return

    if user.state == UserStateEnum.PENDING:
        await message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        return

    user.state = UserStateEnum.PENDING
    await user.asave()

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message.text and await is_has_censor(message.text, ban_words):
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
        gpt_answer = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)
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

    user.balance -= 1
    if user.balance <= 5:
        user.role = UserRoleEnum.BASE
    await user.asave()
    await message.answer(text=f"Баланс в токенах {user.balance}")


@dp.message(MenuState.dalle)
async def dale_handler(message: Message):
    user = await is_user_exist(chat_id=str(message.chat.id))
    suggestion = (
        "🌆Хотите обработать Ваш запрос с помощью CHAT GPT 4, для создания трех вариантов профессиональных промптов?\n"
        "(Стоимость 1 токен)"
    )
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

    user.state = UserStateEnum.READY
    await user.asave()


async def handle_imagine(message, img_url: str | None = None):
    if "\n" in message.text:
        await message.answer("⛔️Промт должен содержать только одну строку⛔️")
        return

    suggestion = (
        "🌆Хочешь обработать запрос с помощью CHAT GPT, для создания трех вариантов профессиональных промптов?\n"
        "(Стоимость 1 токен)"
    )
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
        await user.asave()
        return

    file = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_path=file.file_path)
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token, "Content-Type": "application/json"}

    attachment = await upload_file(file=file, header=header)
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
        last_message_id=message.message_id,
    )

    await new_blend.asave()


async def based_on_photo_imagine(message: Message):
    file = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_path=file.file_path)
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token, "Content-Type": "application/json"}

    attachment = await upload_file(file=file, header=header)
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
        logger.error(image_data.json())
    else:
        logger.error(image_data.text)
        await message.answer("Не удалось загрузить фото")
        return

    img_url = image_data["attachments"][0]["proxy_url"]

    await handle_imagine(message=message, img_url=img_url)


async def describe_handler(message: Message, user: User):
    file = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_path=file.file_path)
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token, "Content-Type": "application/json"}

    attachment = await upload_file(file=file, header=header)
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
