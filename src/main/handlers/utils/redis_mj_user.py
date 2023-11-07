from aiogram import Bot
from aiogram.enums import ParseMode
from decouple import config
from loguru import logger

from main.enums import UserRoleEnum
from main.handlers.queue import r_queue
from main.models import DsMjUser, User
from main.utils import notify_admins
from t_bot.settings import TELEGRAM_TOKEN

bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


class RedisMjUserTokenQueue:
    async def start(self):
        db_senders: list[DsMjUser] = await DsMjUser.objects.get_senders()
        if len(db_senders) != 0:
            if len(db_senders) == 1:
                r_queue.set("sender", db_senders[0].token)
            elif len(db_senders) > 1:
                r_queue.set("base_sender", db_senders[0].token)
                r_queue.set("premium_sender", db_senders[1].token)
        else:
            r_queue.set("sender", config("DISCORD_USER_TOKENS").split(" ")[0])

    async def get_sender_token(self, user: User) -> str:
        if r_queue.get("sender"):
            return (r_queue.get("sender")).decode()
        elif r_queue.get("sender") is None:
            if user.role == UserRoleEnum.BASE:
                return (r_queue.get("base_sender")).decode()
            else:
                return (r_queue.get("premium_sender")).decode()
        else:
            logger.warning("Обновите список миджорни аккаунтов")

    async def update_sender(self, is_fail: bool, user: User):
        if r_queue.get("sender"):
            await self._update_chosen_sender("sender", is_fail)
        elif not r_queue.get("sender"):
            if user.role == UserRoleEnum.BASE:
                await self._update_chosen_sender("base_sender", is_fail)
            else:
                await self._update_chosen_sender("premium_sender", is_fail)
        else:
            admins: list[User] = await User.objects.get_admins()
            for admin in admins:
                await bot.send_message(
                    chat_id=admin.chat_id, text="Миджорни аккаунты закончились, пожалуйста обновите список"
                )
            logger.warning("Обновите список миджорни аккаунтов")

        await self._check_senders_for_availability()

    async def _update_chosen_sender(self, queue_name, is_fail):
        token = (r_queue.get(queue_name)).decode()
        sender = await DsMjUser.objects.get_sender_by_token(token=token)
        if is_fail:
            sender.fail_in_row += 1
            await sender.asave()
            if sender.fail_in_row >= 15:
                sender.is_active = False
                await sender.asave()
                await notify_admins(bot=bot, banned_mj_user=sender)
                r_queue.getdel(queue_name)
        else:
            sender.fail_in_row = 0

    async def _check_senders_for_availability(self):
        sender = r_queue.get("base_sender")
        base_sender = r_queue.get("base_sender")
        premium_sender = r_queue.get("premium_sender")

        if not sender and not base_sender and not premium_sender:
            db_senders: list[DsMjUser] = await DsMjUser.objects.aget_senders()
            if len(db_senders) == 1:
                r_queue.set("sender", db_senders[0].token)
            elif len(db_senders) > 1:
                r_queue.set("base_sender", db_senders[0].token)
                r_queue.set("premium_sender", db_senders[1].token)
            return

        if not sender and (not base_sender or not premium_sender):
            db_senders: list[DsMjUser] = await DsMjUser.objects.aget_senders()
            r_queue.set("sender", db_senders[0].token)
            return
