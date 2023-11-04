from asgiref.sync import sync_to_async
from django.db import models


class BanWordManager(models.Manager):
    @sync_to_async()
    def get_active_ban_words(self):
        res = [word.word for word in self.filter(is_active=True).all()]
        return res


class BanWord(models.Model):
    word: str = models.CharField(null=False, unique=True, verbose_name="Запрещенное слово")
    is_active: bool = models.BooleanField(default=False, verbose_name="Активный")

    objects = BanWordManager()

    def __str__(self):
        name = f"{self.word}[{self.pk}] +" if self.is_active else f"{self.word}[{self.pk}] -"
        return name

    class Meta:
        verbose_name = "Запрещенное слово"
        verbose_name_plural = "Запрещенные слова"
