from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

mj_pay_keyboard_options = [
    types.InlineKeyboardButton(text="10 генераций", callback_data="mjpay_1"),
    types.InlineKeyboardButton(text="20 генераций", callback_data="mjpay_2"),
    types.InlineKeyboardButton(text="55 генераций", callback_data="mjpay_5"),
    types.InlineKeyboardButton(text="110 генераций", callback_data="mjpay_10"),
]

def get_keyboard_from_buttons(buttons):
    builder = InlineKeyboardBuilder()
    for button in buttons:
        builder.row(button)

    return builder.as_markup()


async def get_pay_keyboard(service: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if service == "mj":
        for mj_button in mj_pay_keyboard_options:
            builder.row(mj_button)

    return builder.as_markup()

def get_gen_count(amount: str):
    if amount == "1.00":
        return 10
    if amount == "2.00":
        return 20
    if amount == "5.00":
        return 55
    if amount == "10.00":
        return 110
