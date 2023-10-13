import json
import os
from tempfile import NamedTemporaryFile

import discord
import django
import requests

from main.keyboards import keyboard_interactions

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

from main.models import DiscordQueue  # noqa: E402
from t_bot.settings import TELEGRAM_TOKEN  # noqa: E402


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as", self.user)

    async def on_message(self, message):
        if message.author == self.user or len(message.attachments) == 0:
            return

        prompt = str(message.content).split("**")[1]

        queue = await DiscordQueue.objects.get_queue_by_prompt(prompt=prompt)

        if not queue:
            return

        await self._send_photo_to_telegram(message=message, queue=queue)

    async def _send_photo_to_telegram(self, message, queue: DiscordQueue):
        filename = message.attachments[0].filename
        message_hash = filename.split("_")[-1].split(".")[0]
        file_url = message.attachments[0].url
        raw_image = requests.get(file_url).content

        with NamedTemporaryFile("wb+") as f:
            f.write(raw_image)
            f.seek(0)
            files = {"photo": f}
            data = {"reply_markup": json.dumps(keyboard_interactions)}

            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto?chat_id={queue.telegram_chat_id}",
                files=files,
                data=data,
            )

        await DiscordQueue.objects.update_message_hash(queue=queue, message_hash=message_hash)
        await DiscordQueue.objects.update_message_id(queue=queue, discord_message_id=message.id)


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run("MTE2MDU0NTQ1OTA2NTA3Mzc1NQ.GVi1pf.yl5bG37g4T2otjiHhTiCYctWGO-3NL7YmlVBzw")
