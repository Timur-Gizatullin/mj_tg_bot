from aiogram import types

start_buttons = (
    types.InlineKeyboardButton(text="Midjourney", callback_data="start_mj"),
    types.InlineKeyboardButton(text="DAL-E", callback_data="start_dale"),
    types.InlineKeyboardButton(text="GPT", callback_data="start_gpt"),
    types.InlineKeyboardButton(text="Личный кабинат и оплата", callback_data="start_lk"),
    types.InlineKeyboardButton(text="Реферальная ссылка", callback_data="start_ref"),
    types.InlineKeyboardButton(text="Инструкции, настройки, стили, ракурсы", url="V4"),
    types.InlineKeyboardButton(text="Сайт", url="V4"),
    types.InlineKeyboardButton(text="Чат технической поддержки", url="V4"),
    types.InlineKeyboardButton(text="Наш сайт с огромной базой информации и регулярными обновлениями", url="V4"),
)
