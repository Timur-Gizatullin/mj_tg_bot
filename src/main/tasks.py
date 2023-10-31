import requests
from loguru import logger

from main.handlers.utils.wallet import WALLET_CREATE_ORDER, WALLET_HEADERS
from main.models import Pay, User
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
