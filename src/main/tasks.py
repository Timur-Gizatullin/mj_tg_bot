import json

import requests

from main.enums import UserRoleEnum
from main.models import BanWord, User
from t_bot.celery import app
from t_bot.settings import TELEGRAM_TOKEN


@app.task(bind=True, name="Рассылка")
def send_message_to_users(
    self,
    message: str | None = None,
    role: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    pay_date: int | None = None,
    gen_date: int | None = None,
):
    users = User.objects.get_users_to_send_message(role, limit, offset, pay_date, gen_date)
    for user in users:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={user.chat_id}&text={message}")


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
