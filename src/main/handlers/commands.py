import requests
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from decouple import config

from main.constants import BOT_HOST
from main.enums import AnswerTypeEnum
from main.handlers.utils.interactions import INTERACTION_URL, _trigger_payload
from main.keyboards.pay import get_pay_keyboard
from main.models import BanWord, Prompt, Referral, TelegramAnswer, User
from main.utils import is_has_censor
from t_bot.settings import TELEGRAM_TOKEN

dp = Dispatcher()
bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)


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

    help_message = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.HELP)

    await message.answer(help_message)


@dp.message(Command("referral"))
async def create_referral(message: Message, state) -> None:
    await state.clear()

    referrer = await User.objects.get_user_by_username(username=message.from_user.username)

    referral_key = await Referral.objects.create_referral(referrer=referrer)
    referral = f"{BOT_HOST}{referral_key}"

    await message.answer(f"Ваша ссылка: {referral}")


@dp.message(Command("imagine"))
async def imagine_handler(message: Message, state, command: CommandObject) -> None:
    await state.clear()
    prompt = command.args

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message.text and await is_has_censor(prompt, ban_words):
        await message.answer(censor_message_answer)
        return

    payload = _trigger_payload(
        2,
        {
            "version": "1118961510123847772",
            "id": "938956540159881230",
            "name": "imagine",
            "type": 1,
            "options": [{"type": 3, "name": "prompt", "value": f"#{message.chat.id}# {prompt}"}],
            "attachments": [],
        },
    )
    header = {"authorization": config("DISCORD_USER_TOKEN")}

    requests.post(INTERACTION_URL, json=payload, headers=header)

    await message.answer("Запрос отправлен")


@dp.message(Command("mj_pay"))
async def buy_handler(message: types.Message):
    await message.answer("Выберите один из вариантов", reply_markup=await get_pay_keyboard(service="mj"))
