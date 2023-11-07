from datetime import datetime
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.db import models

from main.models.user import User


class ReferralManager(models.Manager):
    @sync_to_async()
    def create_referral(self, referrer: User) -> "Referral":
        key = str(uuid4())
        new_referral = Referral(referrer=referrer, key=key)
        new_referral.save()

        return new_referral

    @sync_to_async()
    def get_referral(self, referral_key: int) -> "Referral":
        return self.filter(key=referral_key).first()

    @sync_to_async()
    def update_referrer_generations_count(self, referral_key: int) -> None:
        referral = self.filter(key=referral_key).first()

        referral.referrer.balance += 6
        referral.used_count += 1
        referral.referrer.save()

    @sync_to_async()
    def get_referral_by_user(self, user: User) -> "Referral":
        return self.filter(referrer=user).first()

    @sync_to_async()
    def get_referrals(self) -> list["Referral"]:
        return list(self.exclude(name=None).exclude(name="").all())


class Referral(models.Model):
    key: str = models.CharField(unique=True, null=False, verbose_name="Уникальный ключ")
    referrer: User = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="referrals",
        verbose_name="Владелец ссылки",
    )
    name: str = models.CharField(null=True, blank=True, verbose_name="Название")
    used_count = models.IntegerField(default=int(), verbose_name="Колличество переходов")
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name="Время создания")

    objects = ReferralManager()

    def __str__(self):
        return f"{self.referrer.telegram_username}[{self.name}]"

    @sync_to_async()
    def get_referrer(self):
        return self.referrer

    class Meta:
        verbose_name = "Рефферальная ссылка"
        verbose_name_plural = "Реферальные ссылки"
