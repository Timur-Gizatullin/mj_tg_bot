from asgiref.sync import sync_to_async
from django.db import models


class PromptManager(models.Manager):
    @sync_to_async()
    def get_queue_by_prompt(self, prompt: str) -> "Prompt":
        return self.filter(prompt=prompt).order_by("created_at", "telegram_user__role").first()

    @sync_to_async()
    def get_queue_by_message_hash(self, message_hash: str) -> "Prompt":
        return self.filter(message_hash=message_hash).order_by("created_at").first()

    @sync_to_async()
    def delete_queue(self, queue: "Prompt") -> None:
        queue.delete()

    @sync_to_async()
    def update_message_hash(self, queue: "Prompt", message_hash: str) -> None:
        queue.message_hash = message_hash
        queue.save()

    @sync_to_async()
    def update_message_id(self, queue: "Prompt", discord_message_id: str) -> None:
        queue.discord_message_id = discord_message_id
        queue.save()

    @sync_to_async()
    def create_queue(self, **kwargs) -> "Prompt":
        new_queue = Prompt(**kwargs)
        new_queue.save()

        return new_queue


class Prompt(models.Model):
    prompt = models.CharField()
    telegram_chat_id = models.CharField(null=True)
    telegram_user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="prompts")
    discord_message_id = models.CharField(null=True)
    message_hash = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    objects = PromptManager()

    def __str__(self):
        return f"{self.prompt}[{self.pk}]"
