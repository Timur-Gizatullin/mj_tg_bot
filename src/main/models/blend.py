from datetime import datetime

from asgiref.sync import sync_to_async
from django.db import models


class BlendManager(models.Manager):
    @sync_to_async
    def get_blends_by_group_id(self, group_id: int) -> list["Blend"]:
        return list(self.filter(group_id=group_id).all())


class Blend(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="blends")
    group_id: str = models.CharField()
    uploaded_filename: str = models.CharField()
    created_at: datetime = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = BlendManager()
