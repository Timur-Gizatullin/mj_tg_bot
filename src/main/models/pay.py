from datetime import datetime
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db import models


class PayManager(models.Manager):
    def get_unverified_pays(self) -> list["Pay"]:
        return list(self.filter(is_verified=False).all())


class Pay(models.Model):
    amount: Decimal = models.DecimalField(null=False, decimal_places=4, max_digits=12)
    token_count: int = models.IntegerField(null=True)
    pay_id: int = models.IntegerField(null=True)
    is_verified = models.BooleanField(null=True, default=False)
    user = models.ForeignKey("User", on_delete=models.DO_NOTHING, related_name="payments")
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True)

    objects = PayManager()
