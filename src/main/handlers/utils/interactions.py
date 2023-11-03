from typing import Any

import requests
from loguru import logger

from main.handlers.queue import QueueHandler
from main.handlers.utils.const import INTERACTION_URL
from main.handlers.utils.mj_user import MjUserTokenQueue
from main.models import Blend, Prompt
from t_bot.settings import CHANNEL_ID, GUILD_ID

mj_user_token_queue = MjUserTokenQueue()


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


async def send_variation_trigger(variation_index: str, queue: Prompt, message):
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::variation::{variation_index}::{queue.message_hash}"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="variation")


async def send_upsample_trigger(upsample_index: str, queue: Prompt, message, version: str = ""):
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    solo = "::SOLO" if version != "" else ""
    action = "upsample" if version == "" else f"upscale_{version}"
    payload = _trigger_payload(
        3,
        {"component_type": 2, "custom_id": f"MJ::JOB::upsample{version}::{upsample_index}::{queue.message_hash}{solo}"},
        **kwargs,
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action=action)


async def send_reset_trigger(message_id: str, message_hash: str, message):
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::reroll::0::{message_hash}::SOLO"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="reroll")


async def send_vary_trigger(vary_type: str, queue: Prompt, message):
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::{vary_type}::1::{queue.message_hash}::SOLO"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="vary")


async def send_zoom_trigger(zoomout: str, queue: Prompt, message):
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3,
        {"component_type": 2, "custom_id": f"MJ::Outpaint::{int(float(zoomout) * 50)}::1::{queue.message_hash}::SOLO"},
        **kwargs,
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="zoom")


async def send_pan_trigger(direction: str, queue: Prompt, message):
    kwargs = {
        "message_flags": 0,
        "message_id": queue.discord_message_id,
    }
    payload = _trigger_payload(
        3, {"component_type": 2, "custom_id": f"MJ::JOB::pan_{direction}::1::{queue.message_hash}::SOLO"}, **kwargs
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="pan")


async def imagine_trigger(message, prompt):
    payload = _trigger_payload(
        2,
        {
            "version": "1166847114203123795",
            "id": "938956540159881230",
            "name": "imagine",
            "type": 1,
            "options": [{"type": 3, "name": "prompt", "value": f"#{message.chat.id}# {prompt}"}],
            "attachments": [],
        },
    )
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="imagine")


async def describe_reset_trigger(message_id: str, message):
    kwargs = {
        "message_flags": 0,
        "message_id": message_id,
    }
    payload = _trigger_payload(3, {"component_type": 2, "custom_id": "MJ::Picread::Retry"}, **kwargs)
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="describe_retry")


async def blend_trigger(blends: list[Blend], message):
    attachments = []
    options = []
    for i, blend in enumerate(blends):
        logger.debug(i)
        logger.debug(blend)
        attachments.append(
            {
                "id": i,
                "filename": blend.uploaded_filename.split("/")[-1],
                "uploaded_filename": blend.uploaded_filename,
            }
        )
        options.append(
            {"type": 11, "name": f"image{i+1}", "value": i}
        )

    payload = _trigger_payload(
        2,
        {
            "version": "1166847114203123796",
            "id": "1062880104792997970",
            "name": "blend",
            "type": 1,
            "attachments": attachments,
            "options": options,
        },
    )
    logger.debug(attachments)
    token = await mj_user_token_queue.get_sender_token()
    header = {"authorization": token}

    await QueueHandler.include_queue(payload=payload, header=header, message=message, action="describe_retry")
