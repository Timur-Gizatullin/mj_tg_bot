from typing import Any

from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

keyboard_interactions = {
    "inline_keyboard": [
        [
            {
                "text": "V1",
                "callback_data": "V1",
            },
            {
                "text": "V2",
                "callback_data": "V2",
            },
            {
                "text": "V3",
                "callback_data": "V3",
            },
            {
                "text": "V4",
                "callback_data": "V4",
            },
            {
                "text": "🔄",
                "callback_data": "reset",
            },
        ],
        [
            {
                "text": "U1",
                "callback_data": "U1",
            },
            {
                "text": "U2",
                "callback_data": "U2",
            },
            {
                "text": "U3",
                "callback_data": "U3",
            },
            {
                "text": "U4",
                "callback_data": "U4",
            },
        ],
    ]
}

keyboard_solo_interactions = {
    "inline_keyboard": [
        [
            {
                "text": "🪄Vary(Strong)",
                "callback_data": "vary_strong",
            },
            {
                "text": "🪄Vary(Subtle)",
                "callback_data": "vary_subtle",
            },
            {
                "text": "🖌Vary(Region)",
                "callback_data": "vary_region",
            },
        ],
        [
            {
                "text": "🔍Zoom Out 2x",
                "callback_data": "zoom_2",
            },
            {
                "text": "🔍Zoom Out 1.5x",
                "callback_data": "zoom_1.5",
            },
            {
                "text": "🔍Custom Zoom",
                "callback_data": "zoom_custom",
            },
        ],
        [
            {
                "text": "⬅️",
                "callback_data": "pan_left",
            },
            {
                "text": "➡️",
                "callback_data": "pan_right",
            },
            {
                "text": "⬆️",
                "callback_data": "pan_up",
            },
            {
                "text": "⬇️",
                "callback_data": "pan_down",
            },
        ],
    ]
}

keyboard_pan_interactions = {
    "inline_keyboard": [
        [
            {
                "text": "U1",
                "callback_data": "U1",
            },
            {
                "text": "U2",
                "callback_data": "U2",
            },
            {
                "text": "U3",
                "callback_data": "U3",
            },
            {
                "text": "U4",
                "callback_data": "U4",
            },
            {
                "text": "🔄",
                "callback_data": "reset",
            },
        ],
    ]
}

keyboard_solo_pan_interactions = {
    "inline_keyboard": [
        [
            {
                "text": "🔍Zoom Out 2x",
                "callback_data": "zoom_2",
            },
            {
                "text": "🔍Zoom Out 1.5x",
                "callback_data": "zoom_1.5",
            },
            {
                "text": "🔍Custom Zoom",
                "callback_data": "zoom_custom",
            },
        ],
        [
            {
                "text": "⬅️",
                "callback_data": "pan_left",
            },
            {
                "text": "➡️",
                "callback_data": "pan_right",
            },
            {
                "text": "️↔️",
                "callback_data": "zoom_2",
            },
        ],
    ]
}

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


async def get_keyboard(prompt: str, caption: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if prompt.find("Image") != -1 and caption:
        builder.row(*zoom_buttons)
        if caption.find("Pan Right") != -1 or caption.find("Pan Left") != -1:
            builder.row(pan_left_button, pan_right_button, left_right_square_button)
        if caption.find("Pan Up") != -1 or caption.find("Pan Down") != -1:
            builder.row(pan_left_button, pan_right_button, up_down_square_button)

        return builder.as_markup()

    if prompt.find("Image") != -1:
        builder.row(*vary_buttons)
        builder.row(*zoom_buttons)
        builder.row(pan_left_button, pan_right_button, pan_up_button, pan_down_button)

        return builder.as_markup()

    if prompt.find("Pan") != -1:
        builder.row(*upscale_buttons, reset_button)
        return builder.as_markup()

    builder.row(*upscale_buttons, reset_button)
    builder.row(*variations_buttons)

    return builder.as_markup()
