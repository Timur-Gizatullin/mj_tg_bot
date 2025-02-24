from datetime import datetime

from asgiref.sync import sync_to_async
from django.db import models
from loguru import logger


class BlendManager(models.Manager):
    @sync_to_async
    def get_blends_by_group_id(self, group_id: int) -> list["Blend"]:
        return list(self.filter(group_id=group_id).all())

    @sync_to_async()
    def get_latest_blend(self, group_id) -> list["Blend"]:
        return self.filter(group_id=group_id).order_by("created_at").first()

    @sync_to_async()
    def get_blend_by_filenames(self, file_names: list[str]):
        file_name = "".join(file_names)
        logger.debug(file_name)
        blend = self.filter(uploaded_filename=file_name)

        return blend.first()

    @sync_to_async()
    def get_blend_count_by_user(self, start, end, user):
        return self.filter(created_at__gte=start, created_at__lte=end, user=user).count()


class Blend(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="blends", verbose_name="Пользователь")
    group_id: str = models.CharField(verbose_name="ID медиа группы")
    uploaded_filename: str = models.CharField(verbose_name="Имя файла")
    chat_id: str = models.CharField(null=True, verbose_name="ID телеграм чата")
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name="Время создания")

    objects = BlendManager()

    def __str__(self):
        return f"{self.chat_id}[{self.created_at}]"

    class Meta:
        verbose_name = "Объедененное фото"
        verbose_name_plural = "Объедененные фото"
