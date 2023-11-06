import os
import django
from aiogram import Router, types

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import Pay, User  # noqa: E402

stat_router = Router()


@stat_router.callback_query(lambda c: c.data.startswith("stats"))
async def callback_pay(callback: types.CallbackQuery):
    action = callback.data.split("_")[-1]

    if action == "user":
        user_count: int = await User.objects.get_users_count()
        today_user_count: int = await User.objects.get_users_today_count()
        await callback.message.answer(
            f"Количество пользователей: {user_count}\n"
            f"Количество пользователей за сегодня: {today_user_count}\n",
        )

    if action == "ref":
        ref_count: int = await User.objects.get_referrals_count()
        today_ref_count: int = await User.objects.get_referrals_today_count()
        await callback.message.answer(
            f"Количество всех рефералов: {ref_count}\n"
            f"Количество рефералов за сегодня: {today_ref_count}\n",
        )

    await callback.answer()
