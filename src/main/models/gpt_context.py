from datetime import datetime
from typing import Iterable

from asgiref.sync import sync_to_async
from django.db import models


class GptContextManager(models.Manager):
    @sync_to_async()
    def get_gpt_contexts_by_telegram_chat_id(self, telegram_chat_id: str) -> list["GptContext"]:
        return list(self.filter(telegram_chat_id=telegram_chat_id).all())

    @sync_to_async()
    def delete_gpt_contexts(self, gpt_contexts: Iterable["GptContext"]) -> None:
        for gpt_context in gpt_contexts:
            gpt_context.delete()


class GptContext(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="gpt_contexts")
    role: str = models.CharField()
    content: str = models.CharField()
    telegram_chat_id: str = models.CharField()
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = GptContextManager()
