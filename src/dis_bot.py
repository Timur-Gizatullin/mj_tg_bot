import os

import discord
import django
import requests
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from decouple import config
from discord.message import Message
from loguru import logger

from main.enums import UserStateEnum
from main.keyboards.commands import get_commands_keyboard

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.commands import bot  # noqa: E402
from main.keyboards.interactions import get_keyboard  # noqa: E402
from main.models import Describe, Prompt, User  # noqa: E402


class DiscordMiddleWare(discord.Client):
    async def on_ready(self):
        logger.info("Logged on as", self.user)

    async def on_message_edit(self, message_before: Message, message_after: Message):
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
            await bot.send_photo(
                chat_id=describe_object.chat_id,
                photo=image_proxy_url,
                caption=message_after.embeds[0].description,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )

    async def on_message(self, message: Message):
        if message.author == self.user:
            return

        if message.content:
            prompt = str(message.content).split("**")[1]
            chat_id = str(message.content).split("#")[1].split("#")[0]
        else:
            logger.debug("Message content is empty")
            return

        user: User = await User.objects.get_user_by_chat_id(chat_id)

        if len(message.attachments) == 0:
            await bot.send_message(chat_id=chat_id, text=f"Идет генерация... ⌛️\n")
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

        await Prompt.objects.acreate(
            prompt=prompt,
            telegram_chat_id=chat_id,
            telegram_user=telegram_user,
            discord_message_id=message.id,
            message_hash=message_hash,
            caption=message.content,
        )

        caption = f"`{prompt.split('#')[-1]}`" if "#" in prompt else prompt

        document = BufferedInputFile(file=raw_image, filename=f"{message_hash}.png")
        await bot.send_document(
            chat_id=chat_id, document=document, reply_markup=keyboard, caption=caption, parse_mode=ParseMode.MARKDOWN
        )

        kb_links = await get_commands_keyboard("links")
        await bot.send_message(
            chat_id=chat_id, text=f"Баланс в токенах: {telegram_user.balance}", reply_markup=kb_links
        )
        telegram_user.state = UserStateEnum.READY
        await telegram_user.asave()


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordMiddleWare(intents=intents)
    client.run(config("DISCORD_BOT_TOKEN"))
