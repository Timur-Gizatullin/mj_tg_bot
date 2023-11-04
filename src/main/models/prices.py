from asgiref.sync import sync_to_async
from django.db import models

from main.enums import CurrencyEnum, ProductEnum


class PriceManager(models.Manager):
    @sync_to_async
    def get_active_prices_by_product(self, product: ProductEnum) -> list["Price"]:
        return list(self.filter(product=product, is_active=True).order_by("amount").all())


class Price(models.Model):
    quantity: int = models.IntegerField(verbose_name="Колличество")
    product: str = models.CharField(
        choices=ProductEnum.get_choices(), default=ProductEnum.TOKEN, verbose_name="Продукт"
    )
    description: str = models.CharField(verbose_name="Описание")
    amount: float = models.FloatField(verbose_name="Сумма")
    currency: str = models.CharField(
        choices=CurrencyEnum.get_choices(), default=CurrencyEnum.RUB, verbose_name="Валюта"
    )
    is_active: bool = models.BooleanField(default=True, verbose_name="Активный")

    objects = PriceManager()

    def __str__(self):
        return f"{self.quantity} {self.description}"

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
