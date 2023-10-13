from asgiref.sync import sync_to_async
from django.db import models


class DiscordQueueManager(models.Manager):
    @sync_to_async()
    def get_queue_by_prompt(self, prompt: str) -> "DiscordQueue":
        return self.filter(prompt=prompt).order_by("created_at").first()

    @sync_to_async()
    def get_queue_by_telegram_chat_id(self, telegram_chat_id: str) -> "DiscordQueue":
        return self.filter(telegram_chat_id=telegram_chat_id).order_by("created_at").first()

    @sync_to_async()
    def delete_queue(self, queue: "DiscordQueue") -> None:
        queue.delete()

    @sync_to_async()
    def update_message_hash(self, queue: "DiscordQueue", message_hash: str) -> None:
        queue.message_hash = message_hash
        queue.save()

    @sync_to_async()
    def update_message_id(self, queue: "DiscordQueue", discord_message_id: str) -> None:
        queue.discord_message_id = discord_message_id
        queue.save()

    @sync_to_async()
    def create_queue(self, **kwargs) -> "DiscordQueue":
        new_queue = DiscordQueue(**kwargs)
        new_queue.save()

        return new_queue


class DiscordQueue(models.Model):
    prompt = models.CharField()
    telegram_chat_id = models.CharField()
    discord_message_id = models.CharField(null=True)
    message_hash = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    objects = DiscordQueueManager()

    def __str__(self):
        return f"{self.prompt}[{self.pk}]"
