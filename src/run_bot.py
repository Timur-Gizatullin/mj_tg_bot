import asyncio
import logging
import os
import sys

import django
from aiogram import Bot
from aiogram.enums import ParseMode

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.callbacks import callback_router  # noqa: E402
from main.handlers.commands import dp  # noqa: E402
from t_bot.settings import TELEGRAM_TOKEN  # noqa: E402

bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    # And the run events dispatching
    dp.include_router(callback_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
