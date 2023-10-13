from asgiref.sync import sync_to_async
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from main.enums import UserRoleEnum


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
    role = models.IntegerField(choices=UserRoleEnum.get_choices())

    objects = UserManager()

    def __str__(self):
        name = self.email if self.email else self.telegram_username
        return name
