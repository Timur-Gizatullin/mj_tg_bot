from asgiref.sync import sync_to_async
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as AbstractUserManager
from django.db import models
from django.db.models import QuerySet

from main.enums import UserRoleEnum


class UserManager(AbstractUserManager):
    @sync_to_async()
    def get_user_by_username(self, username: str) -> "User":
        return self.filter(telegram_username=username).first()

    @sync_to_async()
    def get_user_by_chat_id(self, chat_id: str) -> "User":
        return self.filter(chat_id=chat_id).first()

    def get_user_by_id(self, chat_id: str) -> "User":
        return self.filter(chat_id=chat_id).first()

    @sync_to_async()
    def get_or_create_async(self, telegram_username: int, chat_id: int) -> "User":
        user = self.filter(telegram_username=telegram_username, chat_id=chat_id).first()
        if user:
            return user
        user = User(telegram_username=telegram_username, username=telegram_username, chat_id=chat_id)
        user.save()

        return user

    def get_users_to_send_message(
        self,
        role: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        pay_date: int | None = None,
        gen_date: int | None = None,
    ):
        q_set: QuerySet = self
        q_set = q_set.filter(role=role) if role else q_set
        q_set = q_set.filter(pay__date__lte=pay_date) if pay_date else q_set
        q_set = q_set.filter(prompt__date__lte=gen_date) if gen_date else q_set
        q_set = q_set.all()
        q_set = q_set[offset:] if offset else q_set
        q_set = q_set[:limit] if limit else q_set

        return q_set


class User(AbstractUser):
    telegram_username: str = models.CharField(unique=True)
    chat_id: str = models.IntegerField(unique=True, null=True)
    generations_count: int = models.IntegerField(null=False, default=10)
    role = models.CharField(choices=UserRoleEnum.get_choices(), default=UserRoleEnum.BASE)

    objects = UserManager()

    def __str__(self):
        name = self.email if self.email else self.telegram_username
        return name


class SiteFilter(admin.SimpleListFilter):
    title = "generations count"
    parameter_name = "generations_count"
    field_name = "generations__count"

    def lookups(self, request, model_admin):
        users = User.objects.all()
        for user in users:
            yield (user.generations_count, user.generations_count)

    def queryset(self, request, queryset):
        generations_count = self.value()
        print(generations_count)
        if not generations_count:
            return queryset
        return queryset.filter(generations_count__lte=generations_count)


class UserAudit(admin.ModelAdmin):
    list_filter = ("role", SiteFilter)
