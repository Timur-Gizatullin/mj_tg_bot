from asgiref.sync import sync_to_async
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as AbstractUserManager
from django.db import models
from django.db.models import QuerySet

from main.enums import UserRoleEnum, UserStateEnum


class UserManager(AbstractUserManager):
    @sync_to_async()
    def get_admins(self):
        return list(self.filter(role=UserRoleEnum.ADMIN).all())
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
        user = User(telegram_username=telegram_username, chat_id=chat_id)
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
    telegram_username: str = models.CharField(unique=True, null=True)
    chat_id: str = models.CharField(unique=True, null=True)
    balance: int = models.IntegerField(null=False, default=15)
    role = models.CharField(choices=UserRoleEnum.get_choices(), default=UserRoleEnum.BASE)
    state = models.CharField(choices=UserStateEnum.get_choices(), default=UserRoleEnum.BASE)
    password = models.CharField(blank=True)

    objects = UserManager()

    def __str__(self):
        name = self.email if self.email else self.telegram_username
        return name

    async def decrease_generations_count(self, token: int):
        self.balance -= token
        await self.asave()


class UserFilter(admin.SimpleListFilter):
    title = "generations count"
    parameter_name = "balance"
    field_name = "balance"

    def lookups(self, request, model_admin):
        users = User.objects.all()
        for user in users:
            yield (user.balance, user.balance)

    def queryset(self, request, queryset):
        balance = self.value()
        print(balance)
        if not balance:
            return queryset
        return queryset.filter(balance__lte=balance)


class UserAudit(admin.ModelAdmin):
    list_filter = ("role", UserFilter)
