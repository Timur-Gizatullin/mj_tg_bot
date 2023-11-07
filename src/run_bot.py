import asyncio
import logging
import os
import sys

import django
from aiogram.types import BotCommand
from loguru import logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.callbacks.dalle import dalle_router  # noqa: E402
from main.handlers.callbacks.gpt import gpt_router  # noqa: E402
from main.handlers.callbacks.menu import menu_router  # noqa: E402
from main.handlers.callbacks.midjourney import mj_router  # noqa: E402
from main.handlers.callbacks.pay import pay_router  # noqa: E402
from main.handlers.callbacks.stats import stat_router  # noqa:E402
from main.handlers.commands import bot, dp  # noqa: E402
from main.handlers.queue import r_queue  # noqa:E402
from main.enums import UserStateEnum  # noqa:E402
from main.models import User  # noqa:E402


async def clear_queues():
    for i in r_queue.lrange("queue", 0, -1):
        logger.debug("Remove elements form queue")
        chat_id = (r_queue.lpop("queue")).decode()
        user = User.objects.filter(chat_id=chat_id, state=UserStateEnum.PENDING).first()
        user.state = UserStateEnum.READY
        user.save()
    for i in r_queue.lrange("release", 0, -1):
        logger.debug("Remove elements form release")
        chat_id = (r_queue.lpop("release")).decode()
        user = User.objects.filter(chat_id=chat_id, state=UserStateEnum.PENDING).first()
        user.state = UserStateEnum.READY
        user.save()


async def main() -> None:
    dp.include_router(menu_router)
    dp.include_router(mj_router)
    dp.include_router(pay_router)
    dp.include_router(gpt_router)
    dp.include_router(dalle_router)
    dp.include_router(stat_router)

    await clear_queues()

    await bot.delete_my_commands()
    await bot.set_my_commands([BotCommand(command="start", description="Главное меню")])

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
