from django.db import models

from main.enums import StatActionEnum


class Stats(models.Model):
    user: int = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        related_name="stats",
    )
    action: StatActionEnum = models.CharField(choices=StatActionEnum.get_choices(), default=None)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name="Время создания")
