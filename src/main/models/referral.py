from uuid import uuid4

from asgiref.sync import sync_to_async
from django.db import models

from main.models.user import User


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
        return self.referrer.telegram_username
