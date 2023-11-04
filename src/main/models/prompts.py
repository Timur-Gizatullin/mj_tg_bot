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
    prompt = models.CharField()
    telegram_chat_id = models.CharField(null=True)
    telegram_user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="prompts")
    discord_message_id = models.CharField(null=True)
    message_hash = models.CharField(null=True)
    caption = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    objects = PromptManager()

    def __str__(self):
        return f"{self.prompt[:60]}[{self.created_at}]"
