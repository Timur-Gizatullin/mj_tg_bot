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

upscale_buttons = (
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
    types.InlineKeyboardButton(text="🖌Vary(Region)", callback_data="vary_region"),
)

zoom_buttons = (
    types.InlineKeyboardButton(text="🔍 Zoom Out 2x", callback_data="zoom_2"),
    types.InlineKeyboardButton(text="🔍 Zoom Out 1.5x", callback_data="zoom_1.5"),
    types.InlineKeyboardButton(text="🔍 Zoom Out Custom", callback_data="zoom_custom"),
)


async def get_keyboard(buttons: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    arrows = []

    if "U1" in buttons and "U2" in buttons and "U3" in buttons and "U4" in buttons:
        builder.row(*upscale_buttons, reset_button)
    if "V1" in buttons and "V2" in buttons and "V3" in buttons and "V4" in buttons:
        builder.row(*variations_buttons)
    if "Vary" in buttons:
        builder.row(*vary_buttons)
    if "Zoom" in buttons:
        builder.row(*zoom_buttons)
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
