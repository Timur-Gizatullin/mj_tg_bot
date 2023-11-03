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
        # for i, file_name in enumerate(file_names):
        #     if i != 0:
        #         blend.filter(uploaded_filename__contains=file_names[i])

        return blend.first()


class Blend(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="blends")
    group_id: str = models.CharField()
    uploaded_filename: str = models.CharField()
    last_message_id: str = models.CharField(null=True)
    chat_id: str = models.CharField(null=True)
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = BlendManager()
