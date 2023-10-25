from typing import Callable

from redis import Redis
from rq import Queue

from main.enums import UserRoleEnum


class QueueHandler:
    base_queue = Queue(name="low", connection=Redis())
    premium_queue = Queue(name="high", connection=Redis())

    async def add_task(self, action: Callable, user_role: UserRoleEnum, **kwargs) -> None:
        if user_role == UserRoleEnum.BASE:
            # self.base_queue.enqueue(action, **kwargs)
            await action(**kwargs)
        else:
            await action(**kwargs)
            # self.premium_queue.enqueue(action, **kwargs)


queue_handler = QueueHandler()
