from datetime import date, datetime, timedelta, timezone

from asgiref.sync import sync_to_async
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as AbstractUserManager
from django.db import models
from django.db.models import QuerySet
from loguru import logger

from main.enums import UserRoleEnum, UserStateEnum


class UserManager(AbstractUserManager):
    @sync_to_async()
    def check_stack_pending_users(self) -> list["User"]:
        pending_users: list[User] = list(self.filter(state=UserStateEnum.PENDING).all())
        cleared_users = []
        for pending_user in pending_users:
            if pending_user.pending_state_at:
                diff = datetime.now(timezone.utc) - pending_user.pending_state_at
                if diff >= timedelta(seconds=15*60):
                    pending_user.pending_state_at = None
                    pending_user.state = UserStateEnum.READY
                    pending_user.save()
                    cleared_users.append(pending_user)
                    logger.debug(f"User {pending_user.state} state has been refreshed")

        return cleared_users

    @sync_to_async()
    def get_today_inactive_user(self):
        return self.filter(is_active=False).filter(gen_date__contains=date.today()).count()

    @sync_to_async()
    def get_month_new_users(self):
        return self.filter(is_active=True).filter(date_joined__month=date.today().month).count()

    @sync_to_async()
    def get_month_stoped_users(self):
        return self.filter(is_active=False).filter(gen_date__month=date.today().month).count()

    @sync_to_async()
    def get_admins(self):
        return list(self.filter(role=UserRoleEnum.ADMIN).all())

    @sync_to_async()
    def get_pending_users(self):
        return list(self.filter(state=UserStateEnum.PENDING).all())

    @sync_to_async()
    def get_active_users_count(self):
        return len(self.exclude(role=UserRoleEnum.ADMIN).filter(is_active=True).all())

    @sync_to_async()
    def get_users_today_count(self):
        return len(self.filter(date_joined__contains=date.today()).exclude(role=UserRoleEnum.ADMIN).all())

    @sync_to_async()
    def get_user_by_chat_id(self, chat_id: str) -> "User":
        return self.filter(chat_id=chat_id).first()

    @sync_to_async()
    def get_referrals_count(self):
        return len(self.exclude(invited_by=None).all())

    @sync_to_async()
    def get_referrals_today_count(self):
        return len(self.filter(date_joined__contains=date.today()).exclude(invited_by=None).all())

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
        q_set = q_set.filter(pay_date__gte=pay_date) if pay_date else q_set
        q_set = q_set.filter(gen_date__gte=gen_date) if gen_date else q_set
        q_set = q_set.all()
        q_set = q_set[offset:] if offset else q_set
        q_set = q_set[:limit] if limit else q_set

        return q_set


class User(AbstractUser):
    username = models.CharField(null=True, unique=True, blank=True)
    telegram_username: str = models.CharField(unique=True, null=True, verbose_name="Юзернейм в телеграме", blank=True)
    chat_id: str = models.CharField(unique=True, null=True, verbose_name="ID чата телеграм")
    balance: int = models.IntegerField(null=False, default=15, verbose_name="Баланс в токенах")
    role = models.CharField(choices=UserRoleEnum.get_choices(), default=UserRoleEnum.BASE, verbose_name="Роль")
    state = models.CharField(choices=UserStateEnum.get_choices(), default=UserStateEnum.READY, verbose_name="Состояние")
    pending_state_at: datetime = models.DateTimeField(blank=True, null=True, verbose_name="Ожидает с")
    is_subscribed: bool = models.BooleanField(default=False, verbose_name="Был подписан на все каналы")
    gen_date: datetime = models.DateTimeField(
        null=True, verbose_name="Дата последней генерации", auto_now=True, blank=True
    )
    pay_date: datetime = models.DateTimeField(null=True, verbose_name="Дата последней оплаты", blank=True)
    password = models.CharField(blank=True, verbose_name="Пароль")
    invited_by = models.ForeignKey(
        "User",
        related_name="invites",
        on_delete=models.DO_NOTHING,
        verbose_name="Пригласил",
        null=True,
        default=None,
        blank=True,
    )
    fail_in_row: str = models.IntegerField(default=0, verbose_name="Ошибок подряд")

    objects = UserManager()

    def __str__(self):
        name = self.email if self.email else self.telegram_username
        return f"{name} #{self.pk}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


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


@admin.action(description="Обновить статус на READY")
def make_ready(modeladmin, request, queryset):
    queryset.update(state=UserStateEnum.READY)


@admin.action(description="Прировнять отрицательный баланс к 5")
def make_balance_five(modeladmin, request, queryset):
    queryset.filter(balance__lt=5).update(balance=5)


class UserAudit(admin.ModelAdmin):
    list_filter = ("role", "state")
    search_fields = ("telegram_username", "chat_id")
    actions = (make_ready, make_balance_five)
