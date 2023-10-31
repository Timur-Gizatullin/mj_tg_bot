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
        return self.filter(key=referral_key, is_active=True).first()

    @sync_to_async()
    def update_referrer_generations_count(self, referral_key: int) -> None:
        referral = self.filter(key=referral_key).first()

        referral.referrer.generations_count += 6
        referral.used_count += 1
        referral.referrer.save()

    @sync_to_async()
    def get_referral_by_user(self, user: User) -> "Referral":
        return self.filter(referrer=user).first()


class Referral(models.Model):
    key: str = models.CharField(unique=True, null=False)
    referrer: User = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="referrals",
        verbose_name="referrer",
    )
    name: str = models.CharField(null=True, blank=True)
    used_count = models.IntegerField(default=int())

    objects = ReferralManager()

    def __str__(self):
        return f"{self.referrer.telegram_username}[{self.name}]"
