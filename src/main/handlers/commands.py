import openai
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from decouple import config
from loguru import logger

from main.constants import BOT_HOST
from main.enums import AnswerTypeEnum
from main.handlers.utils.interactions import (
    INTERACTION_URL,
    _trigger_payload,
    imagine_trigger,
    mj_user_token_queue,
)
from main.keyboards.pay import get_pay_keyboard
from main.models import BanWord, Describe, Referral, TelegramAnswer, User
from main.utils import is_has_censor, put_file, translator, upload_file
from t_bot.settings import TELEGRAM_TOKEN

dp = Dispatcher()
bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)

openai.api_key = config("OPEN_AI_API_KEY")
gpt = openai.Completion


async def is_user_exist(chat_id: str) -> bool:
    user = await User.objects.get_user_by_chat_id(chat_id=chat_id)
    if not user:
        return False
    return True


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

    await Referral.objects.delete_referral_and_update_referrer_generations_count(referral_key=key)

    await start_handler(message, state)


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    await User.objects.get_or_create_async(telegram_username=message.from_user.username, chat_id=message.chat.id)

    initial_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.START)

    await message.answer(initial_message)


@dp.message(Command("help"))
async def help_handler(message: Message, state) -> None:
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")  # TODO добавить сообщение в админку
        return

    help_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.HELP)

    await message.answer(help_message)


@dp.message(Command("referral"))
async def create_referral(message: Message, state) -> None:
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    referrer = await User.objects.get_user_by_username(username=message.from_user.username)

    referral_key = await Referral.objects.create_referral(referrer=referrer)
    referral = f"{BOT_HOST}{referral_key}"

    await message.answer(f"Ваша ссылка: {referral}")


@dp.message(Command("imagine"))
async def imagine_handler(message: Message, state, command: CommandObject) -> None:
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    prompt = translator.translate(command.args)

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message.text and await is_has_censor(prompt, ban_words):
        await message.answer(censor_message_answer)
        return

    await imagine_trigger(message=message, prompt=prompt)

    await message.answer("Запрос отправлен")


@dp.message(Command("mj_pay"))
async def buy_handler(message: types.Message):
    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    await message.answer("Выберите один из вариантов", reply_markup=await get_pay_keyboard(service="mj"))


@dp.message(Command("gpt"))
async def gpt_handler(message: types.Message, state, command: CommandObject):
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    prompt = command.args

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message.text and await is_has_censor(prompt, ban_words):
        await message.answer(censor_message_answer)
        return

    try:
        gpt_answer = await gpt.acreate(model=config("MODEL_ENGINE"), prompt=prompt, max_tokens=config("MAX_TOKENS"))
    except Exception as e:
        logger.error(f"Не удалось получить ответ от ChatGPT из-за непредвиденной ошибки\n{e}")
        await message.answer("ChatGPT временно не доступен, попробуйте позже")
        return

    await message.answer(gpt_answer.choices[0].text)


@dp.message(Command("describe"))
async def describe_handler(message: Message, state):
    await state.clear()

    if not message.photo:
        await message.answer("Пожалуйста, прикрепите фотографию")
        return

    file = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_path=file.file_path)
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token, "Content-Type": "application/json"}

    attachment = await upload_file(file=file, header=header)
    if not attachment:
        await message.answer("Не удалось загрузить файл")
        return

    if not (await put_file(downloaded_file=downloaded_file, attachment=attachment)).ok:
        await message.answer("Не удалось загрузить файл")
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
        await message.answer("Проверьте версию")

    new_describe = Describe(file_name=upload_filename.split("/")[-1], chat_id=str(message.chat.id))
    await new_describe.asave()


@dp.message()
async def handle_any(message: Message, state):
    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    await help_handler(message, state)
