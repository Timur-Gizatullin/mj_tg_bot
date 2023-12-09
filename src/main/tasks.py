import asyncio
import json
from datetime import date, datetime

import requests
import xlsxwriter
from aiogram import Bot
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.types import InputMediaPhoto
from decouple import config
from loguru import logger

from main.enums import MerchantEnum, UserRoleEnum
from main.handlers.utils.redis.redis_mj_user import RedisMjUserTokenQueue
from main.models import (
    BanWord,
    Blend,
    Channel,
    Describe,
    MessageNotify,
    Pay,
    Prompt,
    Referral,
    User,
)
from t_bot.celery import app
from t_bot.settings import TELEGRAM_TOKEN

bot = Bot(token=config("TELEGRAM_TOKEN"), parse_mode=ParseMode.MARKDOWN)


@app.task(bind=True, name="Рассылка")
def send_message_to_users(
    self,
    message_id: int,
    role: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    pay_date: datetime | None = None,
    gen_date: datetime | None = None,
    photos: list[str] | None = None,
):
    users = list(User.objects.get_users_to_send_message(role, limit, offset, pay_date, gen_date))

    async def task(users: list[User], message: str, photos: list[str] | None):
        for user in users:
            try:
                if not photos:
                    response = await bot.send_message(chat_id=user.chat_id, text=message)
                else:
                    if len(photos) == 1:
                        response = await bot.send_photo(chat_id=user.chat_id, photo=photos[0], caption=message)
                    else:
                        media = []
                        for photo in photos:
                            media.append(InputMediaPhoto(media=photo))
                        await bot.send_message(chat_id=user.chat_id, text=message)
                        response = await bot.send_media_group(chat_id=user.chat_id, media=media)
            except Exception as e:
                response = None
            if not response:
                user.is_active = False
                await user.asave()

    message = MessageNotify.objects.filter(pk=message_id).first()

    if message:
        asyncio.get_event_loop().run_until_complete(task(users, message, photos))
    else:
        logger.warning("Указанного сообщения не существует")


@app.task(bind=True, name="Загрузить пользователей")
def load_users(self):
    with open("./main/users.json") as file:
        users = json.load(file)
        for user in users:
            try:
                user_dto = User(
                    telegram_username=user["username"], chat_id=str(user["id"]), balance=user["generations_count"] * 2
                )
                if user["is_premium"]:
                    user_dto.role = UserRoleEnum.PREMIUM
                user_dto.save()
            except:
                pass


@app.task(bind=True, name="Загрузить банворды")
def load_ban_words(self):
    with open("./main/banwords.txt") as file:
        file_data = file.read()
        file_lines = file_data.split("\n")
        for line in file_lines:
            ban_word = BanWord(word=line, is_active=True)
            ban_word.save()


@app.task(bind=True, name="Обновить дс акаунты")
def update_ds_accounts(self):
    asyncio.get_event_loop().run_until_complete(RedisMjUserTokenQueue().start())


@app.task(bind=True, name="Статистика рефералы")
def get_ref_stat(self, chat_id):
    refs: list[Referral] = Referral.objects.exclude(name=None)

    workbook = xlsxwriter.Workbook(f"ref_stat.xlsx")
    worksheet = workbook.add_worksheet()

    worksheet.write("A1", "Реферальная ссылка")
    worksheet.write("B1", "Перешло всего")
    worksheet.write("C1", "Живые")
    worksheet.write("D1", "За сегодня")
    worksheet.write("E1", "За месяц")

    for i, ref in enumerate(refs):
        total = User.objects.filter(invited_by=ref.referrer).count()
        alive = User.objects.exclude(is_active=False).filter(invited_by=ref.referrer).count()
        per_day = User.objects.filter(date_joined__gte=date.today()).filter(invited_by=ref.referrer).count()
        per_month = User.objects.filter(invited_by=ref.referrer).filter(date_joined__month=date.today().month).count()

        worksheet.write(f"A{i + 2}", ref.name)
        worksheet.write(f"B{i + 2}", total)
        worksheet.write(f"C{i + 2}", alive)
        worksheet.write(f"D{i + 2}", per_day)
        worksheet.write(f"E{i + 2}", per_month)

    workbook.close()

    with open(workbook.filename, "rb") as f:
        d = {"document": f}
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", files=d, data={"chat_id": chat_id}
        )
        logger.warning(r)


@app.task(bind=True, name="Статистика")
def get_main_stat(self, start, end, chat_id):
    async def task(start, end, chat_id):
        workbook = xlsxwriter.Workbook(f"user_stat.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.write("A1", "Номер")
        worksheet.write("B1", "Telegram id")
        worksheet.write("C1", "Статус")
        worksheet.write("D1", "Дата старта бота")
        worksheet.write("E1", "колличество генераций за период")
        worksheet.write("F1", "Остаток баланса")
        worksheet.write("G1", "Сумма покупок за период")
        worksheet.write("H1", "Колличество реферралов")

        channels = await Channel.objects.get_stat_channels()

        for i, channel in enumerate(channels):
            worksheet.write(0, 8 + i, channel.label)

        users = await User.objects.get_users_by_date(start, end)

        for i, user in enumerate(users):
            blend_count = await Blend.objects.get_blend_count_by_user(start, end, user)
            describe_count = await Describe.objects.get_count(start, end, user)
            prompt_count = await Prompt.objects.get_count(start, end, user)

            pays = await Pay.objects.get_all_by_filters(start, end, user)

            ref_count = await User.objects.get_ref_count(start, end, user)

            pay_sum = 0

            for pay in pays:
                if pay.merchant == MerchantEnum.YOOKASSA:
                    pay_sum += pay.amount
                else:
                    pay_sum += pay.amount

            worksheet.write(f"A{i + 2}", f"{i}")
            worksheet.write(f"B{i+2}", f"{user.chat_id}")
            worksheet.write(f"C{i+2}", f"{user.state}")
            worksheet.write(f"D{i+2}", f"{user.date_joined}")
            worksheet.write(f"E{i+2}", f"{blend_count+describe_count+prompt_count}")
            worksheet.write(f"F{i+2}", f"{user.balance}")
            worksheet.write(f"G{i+2}", f"{pay_sum}")
            worksheet.write(f"H{i+2}", f"{ref_count}")

            for j, channel in enumerate(channels):
                try:
                    member = await bot.get_chat_member(f"@{channel.channel}", int(user.chat_id))
                    text = "Вступил" if member.status == ChatMemberStatus.LEFT else "Не вступил"
                except Exception as e:
                    text = "Не вступил"
                    logger.warning(f"User {user.telegram_username} has blocked bot")

                worksheet.write(1 + i, j + 8, text)

        workbook.close()

        with open(workbook.filename, "rb") as f:
            d = {"document": f}
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", files=d, data={"chat_id": chat_id}
            )
            logger.warning(r)

    try:
        asyncio.get_event_loop().run_until_complete(task(start, end, chat_id))
    except Exception as e:
        logger.warning(e)
