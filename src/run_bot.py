import asyncio
import logging
import os
import sys

import django
from loguru import logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.queue import r_queue
from main.handlers.callbacks import callback_router  # noqa: E402
from main.handlers.commands import bot, dp  # noqa: E402


async def main() -> None:
    dp.include_router(callback_router)
    for i in r_queue.lrange("queue", 0, -1):
        logger.debug(f"Remove elements form queue")
        r_queue.lpop("queue")
    for i in r_queue.lrange("release", 0, -1):
        logger.debug(f"Remove elements form release")
        r_queue.lpop("release")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
