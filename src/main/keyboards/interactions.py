from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

variations_buttons = (
    types.InlineKeyboardButton(text="V1", callback_data="V1"),
    types.InlineKeyboardButton(text="V2", callback_data="V2"),
    types.InlineKeyboardButton(text="V3", callback_data="V3"),
    types.InlineKeyboardButton(text="V4", callback_data="V4"),
)

upsample_buttons = (
    types.InlineKeyboardButton(text="U1", callback_data="U1"),
    types.InlineKeyboardButton(text="U2", callback_data="U2"),
    types.InlineKeyboardButton(text="U3", callback_data="U3"),
    types.InlineKeyboardButton(text="U4", callback_data="U4"),
)

reset_button = types.InlineKeyboardButton(text="🔄", callback_data="reset")

pan_up_button = types.InlineKeyboardButton(text="⬆️", callback_data="pan_up")
pan_down_button = types.InlineKeyboardButton(text="⬇️", callback_data="pan_down")
pan_left_button = types.InlineKeyboardButton(text="⬅️", callback_data="pan_left")
pan_right_button = types.InlineKeyboardButton(text="➡️️", callback_data="pan_right")

up_down_square_button = types.InlineKeyboardButton(text="↔️", callback_data="zoom_2")
left_right_square_button = types.InlineKeyboardButton(text="↕️", callback_data="zoom_2")

vary_buttons = (
    types.InlineKeyboardButton(text="🪄Vary(Strong)", callback_data="vary_strong"),
    types.InlineKeyboardButton(text="🪄Vary(Subtle)", callback_data="vary_subtle"),
)

zoom_buttons = (
    types.InlineKeyboardButton(text="🔍 Zoom Out 2x", callback_data="zoom_2"),
    types.InlineKeyboardButton(text="🔍 Zoom Out 1.5x", callback_data="zoom_1.5"),
)

upscale_buttons = (
    types.InlineKeyboardButton(text="🔼 Upscale (x2)", callback_data="_v5_2x"),
    types.InlineKeyboardButton(text="⏫ Upscale (x4)", callback_data="_v5_4x"),
)

redo_upscale_buttons = (
    types.InlineKeyboardButton(text="🔼 Redo upscale (x2)", callback_data="_v5_2x"),
    types.InlineKeyboardButton(text="⏫ Redo upscale (x4)", callback_data="_v5_4x"),
)

describe_buttons = (
    types.InlineKeyboardButton(text="1️⃣", callback_data="describe_0"),
    types.InlineKeyboardButton(text="2️⃣", callback_data="describe_1"),
    types.InlineKeyboardButton(text="3️⃣", callback_data="describe_2"),
    types.InlineKeyboardButton(text="4️⃣", callback_data="describe_3"),
)

describe_buttons_all = types.InlineKeyboardButton(text="🎉 Imagine all", callback_data="describe_all")


async def get_keyboard(buttons: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    arrows = []

    if "U1" in buttons and "U2" in buttons and "U3" in buttons and "U4" in buttons:
        builder.row(*upsample_buttons, reset_button)
    if "V1" in buttons and "V2" in buttons and "V3" in buttons and "V4" in buttons:
        builder.row(*variations_buttons)
    if "Vary" in buttons:
        builder.row(*vary_buttons)
    if "⏫" in buttons and "Redo" not in buttons:
        builder.row(*upscale_buttons)
    if "⏫" in buttons and "Redo" in buttons:
        builder.row(*redo_upscale_buttons)
    if "Zoom" in buttons:
        builder.row(*zoom_buttons)
    if "1️⃣" in buttons:
        builder.row(*describe_buttons, reset_button)
        builder.row(describe_buttons_all)
    logger.warning(buttons)
    if "⬅️" in buttons:
        arrows.append(pan_left_button)
    if "➡️" in buttons:
        arrows.append(pan_right_button)
    if "⬆️" in buttons:
        arrows.append(pan_up_button)
    if "⬇️" in buttons:
        arrows.append(pan_down_button)
    if "↔️" in buttons:
        arrows.append(up_down_square_button)
    if "↕️" in buttons:
        arrows.append(left_right_square_button)

    if arrows:
        builder.row(*arrows)

    return builder.as_markup()
