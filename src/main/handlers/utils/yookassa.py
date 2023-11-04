import uuid
from base64 import b64encode

import requests
from decouple import config
from loguru import logger

from main.constants import BOT_HOST
from main.enums import MerchantEnum
from main.models import Pay


async def create_yookassa_invoice(amount: str, description: str, token_count, user):
    user_and_pass = b64encode(f"{config('YOOKASSA_SHOP_ID')}:{config('YOOKASSA_API_KEY')}".encode()).decode("ascii")
    headers = {
        "Authorization": f"Basic {user_and_pass}",
        "Content-type": "application/json",
        "Idempotence-Key": str(uuid.uuid4())
    }

    data = {
        "amount": {
            "value": amount,
            "currency": "RUB"
        },
        "receipt": {
            "customer": {
                "email": "aasemenov098.il@gmail.com"
            },
            "items": [{
                    "description": "Услуга медиа подписки",
                    "quantity": "1.00",
                    "amount": {
                        "value": amount,
                        "currency": "RUB"
                    },
                    "vat_code": 1,
                    "payment_subject": "commodity",
                    "payment_mode": "full_payment"
                },]
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": BOT_HOST
        },
        "description": description
    }

    response = requests.post("https://api.yookassa.ru/v3/payments", json=data, headers=headers)

    if not response.ok:
        raise Exception(response.text)

    response_data = response.json()

    pay_dto = Pay(amount=amount, token_count=token_count, pay_id=response_data["id"], user=user, merchant=MerchantEnum.YOOKASSA)
    await pay_dto.asave()

    return (response_data, pay_dto.pk)


async def is_payment_succeeded(payment_id) -> bool:
    user_and_pass = b64encode(f"{config('YOOKASSA_SHOP_ID')}:{config('YOOKASSA_API_KEY')}".encode()).decode("ascii")
    headers = {
        "Authorization": f"Basic {user_and_pass}",
        "Content-type": "application/json",
        "Idempotence-Key": str(uuid.uuid4())
    }

    response = requests.get(f"https://api.yookassa.ru/v3/payments/{payment_id}", headers=headers)

    if not response.ok:
        logger.error(response.text)
        return False

    response_data = response.json()

    if response_data["status"] == "succeeded":
        return True

    return False
