import json
import os
from tempfile import NamedTemporaryFile

import discord
import django
import requests
from decouple import config
from loguru import logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.handlers.queue import send_action  # noqa: E402
from main.keyboards.interactions import get_keyboard  # noqa: E402
from main.models import Prompt, User  # noqa: E402
from t_bot.settings import TELEGRAM_TOKEN  # noqa: E402


class DiscordMiddleWare(discord.Client):
    async def on_ready(self):
        logger.info("Logged on as", self.user)

    async def setup_hook(self) -> None:
        logger.info("Setup send hook")
        send_action.start()

    async def on_message(self, message):
        if message.author == self.user or len(message.attachments) == 0:
            return

        await self._send_photo_to_telegram(message=message)

    async def _send_photo_to_telegram(self, message):
        prompt = str(message.content).split("**")[1]
        filename = message.attachments[0].filename
        message_hash = filename.split("_")[-1].split(".")[0]

        queue = await Prompt.objects.get_queue_by_message_hash(message_hash=message_hash)

        if not queue:
            queue = await Prompt.objects.get_queue_by_prompt(prompt=prompt)

        file_url = message.attachments[0].url
        raw_image = requests.get(file_url).content
        print(message)
        keyboard = await get_keyboard(prompt=message.content)

        with NamedTemporaryFile(mode="wb+", prefix=f"{message_hash}_", suffix=".png") as f:
            f.write(raw_image)
            f.seek(0)
            files = {"document": f}
            data = {"reply_markup": json.dumps(keyboard), "caption": prompt}

            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument?chat_id={queue.telegram_chat_id}",
                files=files,
                data=data,
            )

        if message.content.find("Image") == -1 and message.content.find("Variations") == -1:
            logger.info("UPDATE")
            await Prompt.objects.update_message_hash(queue=queue, message_hash=message_hash)
            await Prompt.objects.update_message_id(queue=queue, discord_message_id=message.id)
        else:
            logger.info("CREATE")
            telegram_user: User = await User.objects.get_user_by_chat_id(chat_id=queue.telegram_chat_id)
            await Prompt.objects.create_queue(
                prompt=prompt,
                telegram_chat_id=queue.telegram_chat_id,
                telegram_user=telegram_user,
                discord_message_id=message.id,
                message_hash=message_hash,
            )


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordMiddleWare(intents=intents)
    client.run(config("DISCORD_BOT_TOKEN"))
