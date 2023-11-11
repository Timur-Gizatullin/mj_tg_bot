import os

import django
from aiogram import Router, types

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import Pay, User  # noqa: E402

stat_router = Router()


@stat_router.callback_query(lambda c: c.data.startswith("stats"))
async def callback_stats(callback: types.CallbackQuery):
    action = callback.data.split("_")[-1]

    if action == "user":
        active_user_count = await User.objects.get_active_users_count()
        today_user_count = await User.objects.get_users_today_count()
        today_pay_sum = int(await Pay.objects.get_today_pay_sum())
        today_user_stoped = await User.objects.get_today_inactive_user()
        month_user_stopes = await User.objects.get_month_new_users()
        month_stoped_users = await User.objects.get_month_stoped_users()
        month_pay_sum = int(await Pay.objects.get_month_pay_sum())

        answer = (
            f"Колличество активных юзеров: {active_user_count}\n"
                 f"Новые пользователи за сегодня: {today_user_count}\n"
                 f"Сумма оплат за сегодня: {int(today_pay_sum)}\n"
                 f"Остановили бота за сегодня {today_user_stoped}\n"
                 f"Новые пользователи с начала месяца {month_user_stopes}\n"
                 f"Остановили бот с начала месяца: {month_stoped_users}\n"
                 f"Сумма оплат с начала месяца {int(month_pay_sum)}"
        )

        await callback.message.answer(text=answer)

    await callback.answer()
