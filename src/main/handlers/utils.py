from typing import Any

from t_bot.settings import CHANNEL_ID, GUILD_ID

INTERACTION_URL = "https://discord.com/api/v9/interactions"


def _trigger_payload(type_: int, data: dict[str, Any], **kwargs) -> dict[str, Any]:
    payload = {
        "type": type_,
        "application_id": "936929561302675456",
        "guild_id": GUILD_ID,
        "channel_id": CHANNEL_ID,
        "session_id": "cb06f61453064c0983f2adae2a88c223",
        "data": data,
    }
    payload.update(kwargs)
    return payload
