from asgiref.sync import sync_to_async
from django.db import models

from main.enums import AnswerTypeEnum


class TelegramAnswerManager(models.Manager):
    @sync_to_async()
    def get_message_by_type(self, answer_type: AnswerTypeEnum) -> str:
        telegram_answer = self.filter(type=answer_type).first()
        if telegram_answer:
            return telegram_answer.message
        else:
            return "Стандартное сообщение: добавить константы"


class TelegramAnswer(models.Model):
    type = models.CharField(
        choices=AnswerTypeEnum.get_choices(),
        unique=True,
    )
    message = models.TextField()

    objects = TelegramAnswerManager()

    def __str__(self):
        return str(self.type)
