import os

import discord
import django
import requests
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, InputMediaPhoto
from decouple import config
from discord.message import Message
from loguru import logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.commands import bot  # noqa: E402
from main.handlers.queue import QueueHandler
from main.keyboards.commands import resources
from main.keyboards.interactions import get_keyboard  # noqa: E402
from main.models import Blend, Describe, Prompt, User  # noqa: E402

preview_handler = {}


class DiscordMiddleWare(discord.Client):
    async def on_ready(self):
        logger.info("Logged on as", self.user)

    async def on_message_edit(self, message_before: Message, message_after: Message):
        if message_after.content and message_after.attachments:
            prompt = str(message_after.content).split("**")[1]
            chat_id = str(message_after.content).split("#")[1].split("#")[0]
            file_url = message_after.attachments[0].url
            preview = preview_handler.get(f"{chat_id}{prompt}")
            if not preview:
                preview = await bot.send_photo(chat_id=chat_id, photo=file_url)
                preview_handler[f"{chat_id}{prompt}"] = preview.message_id
            else:
                media = InputMediaPhoto(media=file_url)
                await bot.edit_message_media(chat_id=chat_id, message_id=preview, media=media)
            return

        if len(message_after.embeds) == 1 and len(message_before.embeds) == 0:
            logger.debug(message_after.embeds[0].description)
            logger.debug(message_after.embeds[0].image)

            buttons: list[str] = list()
            for component in message_after.components:
                for child in component.children:
                    if child.label:
                        buttons.append(child.label.split(" ")[0])
                    if child.emoji:
                        buttons.append(child.emoji.name)

            keyboard = await get_keyboard(buttons=buttons)

            image_proxy_url = message_after.embeds[0].image.proxy_url
            file_name = image_proxy_url.split("/")[-1]
            describe_object: Describe = await Describe.objects.get_describe_by_file_name(file_name)
            logger.debug("Send edited message to telegram")
            user = await User.objects.get_user_by_chat_id(describe_object.chat_id)

            await bot.send_photo(
                chat_id=describe_object.chat_id,
                photo=image_proxy_url,
                caption=message_after.embeds[0].description,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )
            await QueueHandler.exclude_queue(describe_object.chat_id, telegram_user=user)

    async def on_message(self, message: Message):
        if message.author == self.user:
            return
        if message.content and message.content.count("#") >= 2:
            prompt = str(message.content).split("**")[1]
            chat_id = str(message.content).split("#")[1].split("#")[0]
        elif message.content and message.content.count("#") < 2 and message.attachments:
            links = message.content.split("**")[1].split(" ")
            logger.debug(links)
            file_names = []
            for dirty_link in links:
                clean_link = dirty_link.split("<")[1].split(">")[0]
                file_url = requests.get(clean_link).url
                file_name = file_url.split("/")[-1].split(".")[0]
                file_names.append(file_name)
            blend: Blend = await Blend.objects.get_blend_by_filenames(file_names)
            chat_id = blend.chat_id

            message_hash = message.attachments[0].filename.split("_")[-1].split(".")[0]
            user: User = await User.objects.get_user_by_chat_id(chat_id)
            await Prompt.objects.acreate(
                prompt="BLEND",
                telegram_chat_id=chat_id,
                telegram_user=user,
                discord_message_id=message.id,
                message_hash=message_hash,
            )

            prompt = None
        else:
            logger.debug("Message content is empty")
            return

        if len(message.attachments) == 0:
            return

        logger.debug("Send new_message message to telegram")
        await self._send_photo_to_telegram(message=message, chat_id=chat_id, prompt=prompt)

    async def _send_photo_to_telegram(self, message: Message, chat_id: str, prompt: str):
        filename = message.attachments[0].filename
        message_hash = filename.split("_")[-1].split(".")[0]
        telegram_user: User = await User.objects.get_user_by_chat_id(chat_id=chat_id)

        file_url = message.attachments[0].url
        raw_image = requests.get(file_url).content

        buttons: list[str] = list()
        for component in message.components:
            for child in component.children:
                if child.label:
                    buttons.append(child.label.split(" ")[0])
                if child.emoji:
                    buttons.append(child.emoji.name)

        keyboard = await get_keyboard(buttons=buttons)
        logger.debug(prompt)
        if prompt is not None:
            await Prompt.objects.acreate(
                prompt=prompt,
                telegram_chat_id=chat_id,
                telegram_user=telegram_user,
                discord_message_id=message.id,
                message_hash=message_hash,
                caption=message.content,
            )
            caption = f"`{prompt.split('#')[-1]}`" if "#" in prompt else prompt
        else:
            caption = None

        document = BufferedInputFile(file=raw_image, filename=f"{message_hash}.png")

        try:
            await bot.send_photo(chat_id=chat_id, photo=document)
        except Exception as e:
            logger.error(e)
        try:
            await bot.send_document(
                chat_id=chat_id,
                document=document,
                reply_markup=keyboard,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.error(e)

        preview = preview_handler.pop(f"{chat_id}{prompt}", None)
        logger.debug(preview)

        if preview:
            await bot.delete_message(chat_id=chat_id, message_id=preview)

        logger.debug(message)
        await QueueHandler.exclude_queue(chat_id, telegram_user=telegram_user)

        await bot.send_message(
            chat_id=chat_id,
            text=f"Баланс в токенах: {telegram_user.balance}\n\n*Примеры генераций:* \n{resources}",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordMiddleWare(intents=intents)
    client.run(config("DISCORD_BOT_TOKEN"))
