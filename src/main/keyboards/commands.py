from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

start_buttons = (
    types.InlineKeyboardButton(text="Midjourney", callback_data="start_mj"),
    types.InlineKeyboardButton(text="DAL-E", callback_data="start_dale"),
    types.InlineKeyboardButton(text="GPT", callback_data="start_gpt"),
    types.InlineKeyboardButton(text="Личный кабинат и оплата", callback_data="start_lk"),
    types.InlineKeyboardButton(text="Реферальная ссылка", callback_data="start_ref"),
)

link_buttons = (
    types.InlineKeyboardButton(
        text="Инструкции, лайфхаки, настройки, стили, ракурсы, промпты",
        url="https://www.searchenginejournal.com/alternative-search-engines/271409/",
    ),
    types.InlineKeyboardButton(
        text="Чат технической поддержки", url="https://www.searchenginejournal.com/alternative-search-engines/271409/"
    ),
    types.InlineKeyboardButton(
        text="Наш сайт с огромной базой информации и регулярными обновлениями",
        url="https://www.searchenginejournal.com/alternative-search-engines/271409/",
    ),
)

example_buttons = (
    types.InlineKeyboardButton(
        text="Примеры изображений сгенерированных нашим ботом",
        url="https://www.searchenginejournal.com/alternative-search-engines/271409/",
    ),
    types.InlineKeyboardButton(
        text="Примеры изображений в стиле Cyber Punk",
        url="https://www.searchenginejournal.com/alternative-search-engines/271409/",
    ),
)


async def get_commands_keyboard(type: str):
    builder = InlineKeyboardBuilder()
    if type == "start":
        for button in start_buttons:
            builder.row(button)
    if type == "start_links":
        builder.add(*link_buttons, *example_buttons)
    if type == "links":
        for button in link_buttons:
            builder.row(button)

    return builder.as_markup()
