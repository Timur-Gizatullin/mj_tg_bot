from django.db import models


class MessageNotify(models.Model):
    name: str = models.CharField(
        null=True,
        blank=True,
        verbose_name="Название сообщения",
        help_text="Можете указать название рассылки для удобства",
    )
    text: str = models.TextField(
        null=False,
        blank=False,
        verbose_name="Сообщение для рассылки",
        help_text="Введите сообщение для рассылки и укажите его id в задаче для рассылки",
    )

    def __str__(self):
        return f"{self.name} #{self.pk}"

    class Meta:
        verbose_name = "Собщение для рассылки"
        verbose_name_plural = "Сообщения для рассылки"
