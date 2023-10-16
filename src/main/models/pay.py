from decimal import Decimal

from django.db import models


class Pay(models.Model):
    amount: Decimal = models.DecimalField(null=False, decimal_places=4, max_digits=12)
    item: str = models.CharField()
    user = models.ForeignKey("User", on_delete=models.DO_NOTHING, related_name="payments")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
