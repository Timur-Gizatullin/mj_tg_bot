from typing import Callable

from redis import Redis
from rq import Queue

from main.enums import UserRoleEnum
from t_bot.caches import REDIS_URL


class QueueHandler:
    base_queue = Queue(name="base", connection=Redis(REDIS_URL))
    premium_queue = Queue(name="base", connection=Redis(REDIS_URL))

    async def add_task(self, action: Callable, user_role: UserRoleEnum, **kwargs) -> None:
        if user_role == UserRoleEnum.BASE:
            self.base_queue.enqueue(action, **kwargs)
        else:
            self.premium_queue.enqueue(action, **kwargs)


queue_handler = QueueHandler()
