import os

import discord
import django
import requests
from aiogram.types import BufferedInputFile
from decouple import config
from discord.message import Message
from loguru import logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.commands import bot  # noqa: E402
from main.keyboards.interactions import get_keyboard  # noqa: E402
from main.models import Prompt, User  # noqa: E402


class DiscordMiddleWare(discord.Client):
    async def on_ready(self):
        logger.info("Logged on as", self.user)

    async def on_message(self, message: Message):
        if message.author == self.user:
            return

        prompt = str(message.content).split("**")[1]
        chat_id = str(message.content).split("#")[1].split("#")[0]

        if len(message.attachments) == 0:
            await bot.send_message(chat_id=chat_id, text=f"Запрос {prompt} обрабатывается")
            return

        await self._send_photo_to_telegram(message=message, chat_id=chat_id, prompt=prompt)

    async def _send_photo_to_telegram(self, message: Message, chat_id: str, prompt: str):
        filename = message.attachments[0].filename
        message_hash = filename.split("_")[-1].split(".")[0]
        telegram_user = await User.objects.get_user_by_chat_id(chat_id=chat_id)

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

        document = BufferedInputFile(file=raw_image, filename=f"{message_hash}.png")
        await bot.send_document(chat_id=chat_id, document=document, reply_markup=keyboard, caption=prompt)


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordMiddleWare(intents=intents)
    client.run(config("DISCORD_BOT_TOKEN"))
