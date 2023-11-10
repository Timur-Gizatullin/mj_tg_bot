from datetime import datetime

from asgiref.sync import sync_to_async
from django.db import models


class PromptManager(models.Manager):
    @sync_to_async()
    def get_prompt_by_message_hash(self, message_hash: str) -> "Prompt":
        return self.filter(message_hash=message_hash).order_by("created_at").first()

    @sync_to_async()
    def get_message_by_discord_message_id(self, message_id):
        return self.filter(discord_message_id=message_id).first()


class Prompt(models.Model):
    prompt = models.CharField(verbose_name="Промпт или действие")
    telegram_chat_id = models.CharField(null=True, verbose_name="ID телеграм чата")
    telegram_user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="prompts", verbose_name="Пользователь"
    )
    discord_message_id = models.CharField(null=True, verbose_name="ID сообщения в дискорд")
    message_hash = models.CharField(null=True, verbose_name="хэш сообщения")
    caption = models.CharField(null=True, verbose_name="Подпись")
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True, verbose_name="Время создания")

    objects = PromptManager()

    def __str__(self):
        return f"{self.prompt[:60]}[{self.created_at.strftime('%d/%m/%Y, %H:%M:%S')}]"

    class Meta:
        verbose_name = "Промпт"
        verbose_name_plural = "Промпты"
