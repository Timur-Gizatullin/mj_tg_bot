import asyncio
import random
from asyncio import Task
from typing import Coroutine

from discord.ext import tasks
from loguru import logger

from main.enums import UserRoleEnum


class QueueHandler:
    discord_queue: list[Task] = []
    random_delay = random.randint(1, 10)

    async def add_task(self, action: Coroutine, user_role: UserRoleEnum) -> None:
        new_task = asyncio.create_task(action)
        if user_role == UserRoleEnum.BASE:
            self.discord_queue.append(new_task)
        else:
            self.discord_queue.insert(0, new_task)

    async def release_and_remove_first_action(self) -> None:
        tasks_left = len(self.discord_queue)
        logger.info(f"В очереди {tasks_left} задач")
        if tasks_left != 0:
            current_action = self.discord_queue.pop(0)

            await current_action


queue_handler = QueueHandler()


@tasks.loop(seconds=5.0)
async def send_action():
    await queue_handler.release_and_remove_first_action()
