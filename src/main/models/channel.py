from django.db import models


class Channel(models.Model):
    channel: str = models.CharField(verbose_name="Канал")

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Каналы"
