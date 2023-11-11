from asgiref.sync import sync_to_async
from django.db import models


class ChannelManager(models.Manager):
    @sync_to_async()
    def get_all_channels(self):
        return list(self.exclude(label=None).all())


class Channel(models.Model):
    label: str = models.CharField(
        verbose_name="Название канала", help_text="Это поле будет отображаться на кнопке", null=True
    )
    channel: str = models.CharField(
        verbose_name="Имя канала", help_text="В телеграме обозначается как @Имя_канала, <@> указывать не надо"
    )
    link: str = models.CharField(verbose_name="Ссылка на канал", help_text="Ссылка, прикрепляемая к кнопке")

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Каналы"

    def __str__(self):
        return f"{self.label} #{self.pk}"

    objects = ChannelManager()
