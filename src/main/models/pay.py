from datetime import date, datetime
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.contrib import admin
from django.db import models

from main.enums import MerchantEnum


class PayManager(models.Manager):
    def get_unverified_pays(self) -> list["Pay"]:
        return list(self.filter(is_verified=False).all())

    @sync_to_async()
    def get_unverified_pay_by_id(self, pay_id):
        return self.filter(pk=pay_id, is_verified=False).first()

    @sync_to_async()
    def get_today_pay_sum(self):
        yookassa_pays = (
            self.filter(merchant=MerchantEnum.YOOKASSA)
            .exclude(is_verified=False)
            .filter(created_at__contains=date.today())
        )
        wallet_pays = (
            self.filter(merchant=MerchantEnum.WALLET)
            .exclude(is_verified=False)
            .filter(created_at__contains=date.today())
        )

        total_sum = 0

        for yookassa_pay in yookassa_pays:
            total_sum += yookassa_pay.amount

        for wallet_pay in wallet_pays:
            total_sum += wallet_pay.amount

        return total_sum

    @sync_to_async()
    def get_month_pay_sum(self):
        yookassa_pays = (
            self.filter(merchant=MerchantEnum.YOOKASSA)
            .exclude(is_verified=False)
            .filter(created_at__month=date.today().month)
        )
        wallet_pays = (
            self.filter(merchant=MerchantEnum.WALLET)
            .exclude(is_verified=False)
            .filter(created_at__month=date.today().month)
        )

        total_sum = 0

        for yookassa_pay in yookassa_pays:
            total_sum += yookassa_pay.amount

        for wallet_pay in wallet_pays:
            total_sum += wallet_pay.amount

        return total_sum

    @sync_to_async()
    def get_all_by_filters(self, start, end, user):
        return list(self.filter(is_verified=True, user=user, created_at__gte=start, created_at__lte=end).all())


class Pay(models.Model):
    amount: Decimal = models.DecimalField(null=False, decimal_places=4, max_digits=12, verbose_name="Сумма оплаты")
    token_count: int = models.IntegerField(null=True, verbose_name="Эквивалент в токенах")
    pay_id: int = models.CharField(null=True, verbose_name="ID оплаты в провайдере")
    is_verified = models.BooleanField(null=True, default=False, verbose_name="Подтвержден")
    user = models.ForeignKey("User", on_delete=models.DO_NOTHING, related_name="payments", verbose_name="Пользователь")
    merchant = models.CharField(choices=MerchantEnum.get_choices(), null=True, verbose_name="Провайдер")
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True, verbose_name="Время создания")

    objects = PayManager()

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"{int(self.amount)} руб. [{self.created_at.strftime('%d/%m/%Y, %H:%M:%S')}]"


class PayAudit(admin.ModelAdmin):
    list_filter = ("merchant", "is_verified")
    search_fields = ("user",)
