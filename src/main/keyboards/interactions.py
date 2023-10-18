from typing import Any

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


async def get_keyboard(prompt: str) -> dict[str, Any]:
    if prompt.find("Image") != -1:
        return keyboard_solo_pan_interactions
    if prompt.find("Image") != -1:
        return keyboard_solo_interactions
    if prompt.find("Pan") != -1:
        return keyboard_pan_interactions

    return keyboard_interactions
