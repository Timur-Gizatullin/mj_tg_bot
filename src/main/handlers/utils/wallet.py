import requests
from decouple import config
from loguru import logger


async def get_pay_link(amount: str, description: str, customer_id: str) -> str | None:
    headers = {
     'Wpay-Store-Api-Key': config("WALLET_API_KEY"),
     'Content-Type': 'application/json',
     'Accept': 'application/json',
    }

    payload = {
      'amount': {
        'currencyCode': 'USD',
        'amount': amount,
      },
      'description': description,
      'externalId': 'XXX-YYY-ZZZ',  # ID счета на оплату в вашем боте
      'timeoutSeconds': 60 * 60 * 24,
      'customerTelegramUserId': customer_id,
      'returnUrl': 'https://t.me/MJBOTTESTbot',
      'failReturnUrl': 'https://t.me/wallet',
    }

    response = requests.post(
      "https://pay.wallet.tg/wpay/store-api/v1/order",
      json=payload, headers=headers, timeout=10
    )
    data = response.json()

    if (response.status_code != 200) or (data['status'] not in ["SUCCESS", "ALREADY"]):
        logger.warning("# code: %s json: %s".format(response.status_code, data))
        return None

    return data['data']['payLink']