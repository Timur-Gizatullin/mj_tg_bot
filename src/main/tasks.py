import json
from datetime import date, datetime

import requests
import xlsxwriter
from aiogram import Bot
from asgiref.sync import async_to_sync
from decouple import config
from loguru import logger

from main.enums import UserRoleEnum
from main.handlers.utils.redis_mj_user import RedisMjUserTokenQueue
from main.models import BanWord, Blend, Describe, Pay, Prompt, Referral, User
from t_bot.celery import app
from t_bot.settings import TELEGRAM_TOKEN

bot = Bot(token=config("TELEGRAM_TOKEN"))


@app.task(bind=True, name="Рассылка")
def send_message_to_users(
    self,
    message: str | None = None,
    role: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    pay_date: datetime | None = None,
    gen_date: datetime | None = None,
):
    users = User.objects.get_users_to_send_message(role, limit, offset, pay_date, gen_date)
    for user in users:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={user.chat_id}&text={message}"
        )
        if not response.ok:
            user.is_active = False
            user.save()


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
    async_to_sync(RedisMjUserTokenQueue().start)()


@app.task(bind=True, name="Статистика рефералы")
def get_ref_stat(self, chat_id):
    refs: list[Referral] = Referral.objects.exclude(name=None)

    workbook = xlsxwriter.Workbook(f"stat/ref/{datetime.now()}_ref_stat.xlsx")
    worksheet = workbook.add_worksheet()

    worksheet.write("A1", "Реферальная ссылка")
    worksheet.write("B1", "Перешло всего")
    worksheet.write("C1", "Живые")
    worksheet.write("D1", "За сегодня")
    worksheet.write("E1", "За месяц")

    for i, ref in enumerate(refs):
        total = User.objects.filter(invited_by=ref.referrer).count()
        alive = User.objects.exclude(is_active=False).filter(invited_by=ref.referrer).count()
        per_day = User.objects.filter(date_joined__gte=date.today()).count()
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
    workbook = xlsxwriter.Workbook(f"stat/main/{datetime.now()}_ref_stat.xlsx")
    worksheet = workbook.add_worksheet()

    worksheet.write("A1", "Номер")
    worksheet.write("B1", "Telegram никнейм")
    worksheet.write("C1", "Статус")
    worksheet.write("D1", "Дата старта бота")
    worksheet.write("E1", "колличество генераций за период")
    worksheet.write("F1", "Остаток баланса")
    worksheet.write("G1", "Сумма покупок за период")
    worksheet.write("H1", "Колличество реферралов")

    users = User.objects.filter(gen_date__gte=start, gen_date__lte=end).all()

    for i, user in enumerate(users):
        blend_count = Blend.objects.filter(created_at__gte=start, created_at__lte=end, user=user).count()
        describe_count = Describe.objects.filter(
            created_at__gte=start, created_at__lte=end, chat_id=user.chat_id
        ).count()
        prompt_count = Prompt.objects.filter(created_at__gte=start, created_at__lte=end, telegram_user=user).count()

        pays = Pay.objects.filter(is_verified=True, user=user, created_at__gte=start, created_at__lte=end).all()

        ref_count = User.objects.filter(date_joined__gte=start, date_joined__lte=end, invited_by=user).count()

        pay_sum = 0

        for pay in pays:
            pay_sum += pay.amount

        worksheet.write(f"A{i + 2}", f"{i}")
        worksheet.write(f"B{i+2}", f"{user.username}")
        worksheet.write(f"C{i+2}", f"{user.state}")
        worksheet.write(f"D{i+2}", f"{user.date_joined}")
        worksheet.write(f"E{i+2}", f"{blend_count+describe_count+prompt_count}")
        worksheet.write(f"F{i+2}", f"{user.balance}")
        worksheet.write(f"G{i+2}", f"{pay_sum}")
        worksheet.write(f"H{i+2}", f"{ref_count}")

    workbook.close()

    with open(workbook.filename, "rb") as f:
        d = {"document": f}
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", files=d, data={"chat_id": chat_id}
        )
        logger.warning(r)
