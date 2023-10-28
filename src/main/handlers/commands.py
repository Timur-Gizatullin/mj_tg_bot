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
from main.enums import AnswerTypeEnum
from main.handlers.utils.interactions import (
    INTERACTION_URL,
    _trigger_payload,
    blend_trigger,
    mj_user_token_queue,
)
from main.keyboards.commands import get_commands_keyboard
from main.keyboards.pay import get_pay_keyboard
from main.models import BanWord, Blend, Describe, Referral, TelegramAnswer, User
from main.utils import (
    BlendStateMachine,
    is_has_censor,
    put_file,
    translator,
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

    await Referral.objects.delete_referral_and_update_referrer_generations_count(referral_key=key)

    await start_handler(message, state)


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    existing_user = await User.objects.get_user_by_username(username=message.from_user.username)

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
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
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

    referral = await Referral.objects.create_referral(referrer=referrer)
    referral_link = f"{BOT_HOST}{referral.key}"

    await message.answer(f"Ваша ссылка: {referral_link}")


@dp.message(Command("imagine"))
async def imagine_handler(message: Message, state, command: CommandObject) -> None:
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    prompt = translator.translate(command.args)

    if prompt == "":
        await message.answer("Добавьте описание")
        return

    ban_words = await BanWord.objects.get_active_ban_words()
    censor_message_answer = await TelegramAnswer.objects.get_message_by_type(answer_type=AnswerTypeEnum.CENSOR)

    if message.text and await is_has_censor(prompt, ban_words):  # TODO исправить
        await message.answer(censor_message_answer)
        return

    prompt = prompt.replace(" ", ".")

    suggestion = (
        "Хотите обработать ваш запрос с помощью CHAT GPT для создания трех вариантов профессиональных промптов? "
        "(Стоимость 1 токен)"
    )

    builder = InlineKeyboardBuilder()
    prompt_buttons = (
        types.InlineKeyboardButton(text="Обработать с CHAT GPT", callback_data=f"suggestion_gpt_{prompt}"),
        types.InlineKeyboardButton(text="Оставить мой", callback_data=f"suggestion_stay_{prompt}"),
    )
    kb = builder.row(*prompt_buttons)

    await message.answer(suggestion, reply_markup=kb.as_markup())


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
        gpt_answer = await gpt.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Who won the world series in 2020?"},
                {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                {"role": "user", "content": "Where was it played?"},
            ],
        )  # TODO доделать
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
        logger.error("Check out ds version")
        await message.answer("Что-то пошло не так")
        return

    new_describe = Describe(file_name=upload_filename.split("/")[-1], chat_id=str(message.chat.id))
    await new_describe.asave()


@dp.message(Command("blend"))
async def blend_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer("Отправьте отдельным сообщением сгруппированное фото")

    await state.set_state(BlendStateMachine.image)


@dp.message(BlendStateMachine.image)
async def blend_image_state_handler(message: Message, state: FSMContext):
    user = await is_user_exist(chat_id=str(message.chat.id))
    if not user:
        await message.answer("Напишите боту /start")
        return

    if message.text and message.text.startswith("отмена"):
        await message.answer("Отмена прошла успешна")
        await state.clear()
        return
    if message.text and message.text.startswith("перемешать"):
        await blend_state_handler(message, state)
        return

    if not message.media_group_id:
        await message.answer("Пожалуйста, отправьте фотографии группой")
        return
    logger.error(message.media_group_id)

    if not message.photo:
        await message.answer(
            (
                f"Пожалуйста, прикрепите от двух до 4 фотографий и напишите `отмена {message.media_group_id}` "
                f"или `перемешать {message.media_group_id}`, когда все фотографии будут загружены"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
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


@dp.message(BlendStateMachine.blend)
async def blend_state_handler(message: Message, state: FSMContext):
    logger.debug("ASD")
    user = await is_user_exist(chat_id=str(message.chat.id))
    if not user:
        await message.answer("Напишите боту /start")
        return

    group_id = message.text.split(" ")[-1]
    blends = await Blend.objects.get_blends_by_group_id(group_id)

    await blend_trigger(blends)
    await state.clear()


@dp.message()
async def handle_any(message: Message, state):
    await state.clear()

    if not await is_user_exist(chat_id=str(message.chat.id)):
        await message.answer("Напишите боту /start")
        return

    await help_handler(message, state)
