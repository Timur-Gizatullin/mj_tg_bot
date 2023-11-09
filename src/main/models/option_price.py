from asgiref.sync import sync_to_async
from django.db import models

from main.enums import CurrencyEnum, PriceEnum


class OptionPriceManager(models.Manager):
    @sync_to_async()
    def get_price_by_product(self, product):
        return self.filter(product=product).first()


class OptionPrice(models.Model):
    product = models.CharField(choices=PriceEnum.get_choices(), verbose_name="Опция")
    price = models.IntegerField(verbose_name="Цена")

    def __str__(self):
        return f"{self.product} {self.price}"

    objects = OptionPriceManager()

    class Meta:
        verbose_name = "Цена"
        verbose_name_plural = "Цены"
