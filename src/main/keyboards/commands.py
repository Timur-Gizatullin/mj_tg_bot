from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

resources = """
💡 [Инструкции, промпты и стили](https://t.me/MidjourneyFAQ/5)
🌆 [Примеры генераций](https://t.me/Midjo_art)
🤖 [Примеры генераций в стиле CyberPunk](https://t.me/artcyberpunk) 
🌐 [Наш сайт](https://midjourneypromt.com) 
❓ [Чат поддержки](https://t.me/Midjourneybot_chat)
"""

start_buttons = (
    types.InlineKeyboardButton(text="Midjourney", callback_data="start_mj"),
    types.InlineKeyboardButton(text="DAL-E", callback_data="start_dale"),
    types.InlineKeyboardButton(text="GPT", callback_data="start_gpt"),
    types.InlineKeyboardButton(text="Личный кабинат и оплата", callback_data="start_lk"),
    types.InlineKeyboardButton(text="Реферальная ссылка", callback_data="start_ref"),
)
cancel_builder = InlineKeyboardBuilder()
cancel_kb = cancel_builder.row(types.InlineKeyboardButton(text="Отмена", callback_data="cancel-job"))


async def get_commands_keyboard(type: str):
    builder = InlineKeyboardBuilder()
    if type == "start":
        for button in start_buttons:
            builder.row(button)

    return builder.as_markup()
