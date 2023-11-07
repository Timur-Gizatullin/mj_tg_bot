from asgiref.sync import sync_to_async
from django.db import models


class DsMjUserManager(models.Manager):
    def get_senders(self):
        return list(self.filter(is_active=True).all())

    @sync_to_async()
    def aget_senders(self):
        return list(self.filter(is_active=True).all())

    @sync_to_async()
    def get_sender_by_token(self, token):
        return self.filter(token=token).first()


class DsMjUser(models.Model):
    name: str = models.CharField(blank=True, null=True, verbose_name="Имя")
    token: str = models.CharField(unique=True, null=False, verbose_name="Токен")
    is_active: str = models.BooleanField(default=True, verbose_name="Активный")
    fail_in_row: str = models.IntegerField(default=0, verbose_name="Ошибок подряд")

    class Meta:
        verbose_name = "Дискорд аккаунт"
        verbose_name_plural = "Дискорд аккаунты"

    def __str__(self):
        active = "Активный" if self.is_active else "Не актинвый"
        return f"{self.name} #{self.pk} [{active}]"

    objects = DsMjUserManager()
