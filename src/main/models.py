from uuid import uuid4

from asgiref.sync import sync_to_async
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from main.enums import AnswerTypeEnum


class UserManager(BaseUserManager):
    @sync_to_async()
    def get_user_by_username(self, username: str) -> "User":
        return self.filter(telegram_username=username).first()

    @sync_to_async()
    def get_or_create_async(self, telegram_username: int, chat_id: int) -> "User":
        user = self.filter(telegram_username=telegram_username, chat_id=chat_id).first()
        if user:
            return user
        user = User(telegram_username=telegram_username, username=telegram_username, chat_id=chat_id)
        user.save()

        return user


class User(AbstractUser):
    telegram_username: str = models.CharField(unique=True)
    chat_id: int = models.IntegerField(unique=True, null=True)
    generations_count: int = models.IntegerField(null=False, default=10)

    objects = UserManager()

    def __str__(self):
        name = self.email if self.email else self.telegram_username
        return name


class ReferralManager(models.Manager):
    @sync_to_async()
    def create_referral(self, referrer: User) -> str:
        key = str(uuid4())
        new_referral = Referral(referrer=referrer, key=key)
        new_referral.save()

        return new_referral.key

    @sync_to_async()
    def get_referral(self, referral_key: int) -> "Referral":
        return self.filter(key=referral_key).first()

    @sync_to_async()
    def delete_referral_and_update_referrer_generations_count(self, referral_key: int) -> None:
        referral = self.filter(key=referral_key).first()

        referral.referrer.generations_count += 2
        referral.referrer.save()

        referral.delete()


class Referral(models.Model):
    key: str = models.CharField(unique=True, null=False)
    referrer: User = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="referrals",
        verbose_name="referrer",
    )

    objects = ReferralManager()

    def __str__(self):
        return self.referrer.username


class BanWordManager(models.Manager):
    @sync_to_async()
    def get_active_ban_words(self):
        res = [word.word for word in self.filter(is_active=True).all()]
        return res


class BanWord(models.Model):
    word: str = models.CharField(null=False, unique=True)
    is_active: bool = models.BooleanField(default=False)

    def __str__(self):
        name = f"{self.word}[{self.pk}] +" if self.is_active else f"{self.word}[{self.pk}] -"
        return name

    objects = BanWordManager()


class TelegramAnswerManager(models.Manager):
    @sync_to_async()
    def get_message_by_type(self, answer_type: AnswerTypeEnum) -> str:
        telegram_answer = self.filter(type=answer_type).first()
        if telegram_answer:
            return telegram_answer.message
        else:
            return "Стандартное сообщение: добавить константы"


class TelegramAnswer(models.Model):
    type = models.CharField(
        choices=AnswerTypeEnum.get_choices(),
        unique=True,
    )
    message = models.TextField()

    objects = TelegramAnswerManager()

    def __str__(self):
        return str(self.type)


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
