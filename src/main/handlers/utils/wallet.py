import requests
from decouple import config
from loguru import logger

from main.constants import BOT_HOST
from main.enums import MerchantEnum
from main.models import Pay, User

WALLET_PREVIEW_LINK = "https://pay.wallet.tg/wpay/store-api/v1/order/preview"
WALLET_CREATE_ORDER = "https://pay.wallet.tg/wpay/store-api/v1/order"
WALLET_HEADERS = {
    "Wpay-Store-Api-Key": config("WALLET_API_KEY"),
    "Content-Type": "application/json",
    "Accept": "application/json",
}


async def get_pay_link(
    amount: str, description: str, customer_id: str, chat_id: str, token_count: int, externalId
) -> str | None:
    payload = {
        "amount": {
            "currencyCode": "USD",
            "amount": amount,
        },
        "description": description,
        "externalId": externalId,
        "timeoutSeconds": 60 * 60 * 24,
        "customerTelegramUserId": customer_id,
        "returnUrl": BOT_HOST,
        "failReturnUrl": "https://t.me/wallet",
    }

    response = requests.post(WALLET_CREATE_ORDER, json=payload, headers=WALLET_HEADERS, timeout=60)
    data = response.json()
    logger.debug(data)
    if (response.status_code != 200) or (data["status"] not in ["SUCCESS", "ALREADY"]):
        logger.warning("# code: {} json: {}".format(response.status_code, data))
        return None

    pay_id = data["data"]["id"]
    user: User = await User.objects.get_user_by_chat_id(chat_id)
    logger.debug("create pay")
    pay_dto = Pay(amount=amount, token_count=token_count, pay_id=pay_id, user=user, merchant=MerchantEnum.WALLET)
    await pay_dto.asave()
    logger.debug("return paylink")

    return (data["data"]["payLink"], pay_dto.pk)
