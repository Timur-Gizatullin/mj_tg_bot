import asyncio
import logging
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.callbacks import callback_router  # noqa: E402
from main.handlers.commands import bot, dp  # noqa: E402


async def main() -> None:
    dp.include_router(callback_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
