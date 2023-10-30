import openai
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from decouple import config
from loguru import logger

from main.constants import BOT_HOST
from main.enums import AnswerTypeEnum, UserStateEnum
from main.handlers.utils.interactions import (
    INTERACTION_URL,
    _trigger_payload,
    blend_trigger,
    mj_user_token_queue,
)
from main.keyboards.commands import get_commands_keyboard
from main.models import (
    BanWord,
    Blend,
    Describe,
    GptContext,
    Referral,
    TelegramAnswer,
    User,
)
from main.utils import (
    BlendStateMachine,
    MenuState,
    callback_data_util,
    is_has_censor,
    put_file,
    upload_file,
)
from t_bot.settings import TELEGRAM_TOKEN

dp = Dispatcher()
bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)

openai.api_key = config("OPEN_AI_API_KEY")
gpt = openai.ChatCompletion


async def is_user_exist(chat_id: str) -> User | None:
    user = await User.objects.get_user_by_chat_id(chat_id=chat_id)
    return user


@dp.message(CommandStart(deep_link=True))
async def deep_start(message: Message, command: CommandObject, state: FSMContext):
    key = command.args

    new_user = await User.objects.get_user_by_username(username=message.from_user.username)

    if new_user:
        await message.answer("Вы уже зарегестрированы в нашей системе")
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

    existing_user: User = await User.objects.get_user_by_username(username=message.from_user.username)

    if not existing_user:
        await User.objects.get_or_create_async(telegram_username=message.from_user.username, chat_id=message.chat.id)

    initial_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.START)

    start_kb = await get_commands_keyboard("start")

    await message.answer(initial_message, reply_markup=start_kb)

    links_kb = await get_commands_keyboard("start_links")

    await message.answer(
        "Запуская данный бот Вы даете согласие на правила использования нашего сервиса.", reply_markup=links_kb
    )


@dp.message(Command("help"))
async def help_handler(message: Message, state) -> None:
    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    help_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.HELP)

    await message.answer(help_message)


@dp.message(Command("referral"))
async def create_referral(message: Message, state) -> None:
    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    referrer = await User.objects.get_user_by_username(username=message.from_user.username)

    referral = await Referral.objects.create_referral(referrer=referrer)
    referral_link = f"{BOT_HOST}{referral.key}"

    await message.answer(f"Ваша ссылка: {referral_link}")


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

    if message.text and not message.photo and not message.media_group_id:
        await handle_imagine(message)
    elif message.photo and not message.text and not message.media_group_id:
        await describe_handler(message, user)
    elif message.media_group_id and not message.text and not message.photo:
        await blend_images_handler(message)

    user.state = UserStateEnum.READY
    await user.asave()


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
    await user.asave()


@dp.message(BlendStateMachine.blend)
async def blend_state_handler(message: Message, state: FSMContext):
    user = await is_user_exist(chat_id=str(message.chat.id))
    if not user:
        await message.answer("Напишите боту /start")
        return

    group_id = message.text.split(" ")[-1]
    blends = await Blend.objects.get_blends_by_group_id(group_id)

    await blend_trigger(blends)
    await state.set_state(MenuState.mj)

    user.state = UserStateEnum.READY
    await user.asave()


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
        types.InlineKeyboardButton(text="CHAT GPT", callback_data=f"dalle_suggestion_gpt_{message.chat.id}-{message.message_id}"),
        types.InlineKeyboardButton(text="Оставить мой", callback_data=f"dalle_suggestion_stay_{message.chat.id}-{message.message_id}"),
    )
    kb = builder.row(*prompt_buttons)
    await message.answer(suggestion, reply_markup=kb.as_markup())

    user.state = UserStateEnum.READY
    await user.asave()


@dp.message()
async def handle_any(message: Message, state):
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    await help_handler(message, state)


async def handle_imagine(message):
    suggestion = (
        "🌆Хотите обработать Ваш запрос с помощью CHAT GPT 4, для создания трех вариантов профессиональных промптов?\n"
        "(Стоимость 1 токен)"
    )

    callback_data_util[f"{message.chat.id}-{message.message_id}"] = message.text
    builder = InlineKeyboardBuilder()
    prompt_buttons = (
        types.InlineKeyboardButton(text="CHAT GPT", callback_data=f"suggestion_gpt_{message.chat.id}-{message.message_id}"),
        types.InlineKeyboardButton(text="Оставить мой", callback_data=f"suggestion_stay_{message.chat.id}-{message.message_id}"),
    )
    kb = builder.row(*prompt_buttons)
    await message.answer(suggestion, reply_markup=kb.as_markup())


@dp.message(BlendStateMachine.image)
async def blend_images_handler(message: Message):
    user = await is_user_exist(chat_id=str(message.chat.id))
    if not user:
        await message.answer("Напишите боту /start")
        user.state = UserStateEnum.PENDING
        await user.asave()
        return

    if message.text and message.text.startswith("отмена"):
        await message.answer("Отмена прошла успешна")
        user.state = UserStateEnum.READY
        await user.asave()
        return
    if message.text and message.text.startswith("перемешать"):
        await blend_state_handler(message)
        user.state = UserStateEnum.PENDING
        await user.asave()
        return

    if not message.photo:
        await message.answer("Пожалуйста, прикрепите от двух до 4 фотографий и напишите")
        user.state = UserStateEnum.READY
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

    new_blend = Blend(user=user, group_id=message.media_group_id, uploaded_filename=upload_filename)
    await new_blend.asave()

    await message.answer(
        (
            f"Когда все фотографии загрузятся напишите `отмена {message.media_group_id}` "
            f"или `перемешать {message.media_group_id}`, когда все фотографии будут загружены"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await message.answer("фото загружено")


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

    if not requests.post(INTERACTION_URL, json=payload, headers=header).ok:
        logger.error("Check out ds version")
        await message.answer("Что-то пошло не так")
        user.state = UserStateEnum.READY
        await user.asave()
        return

    new_describe = Describe(file_name=upload_filename.split("/")[-1], chat_id=str(message.chat.id))
    await new_describe.asave()
