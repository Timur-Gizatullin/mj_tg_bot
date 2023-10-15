from asgiref.sync import sync_to_async
from django.db import models


class MjUserManager(models.Manager):
    @sync_to_async()
    def get_mj_users(self) -> list["MjUser"]:
        return self.filter(is_banned=False).all()


class MjUser(models.Model):
    token: str = models.CharField(unique=True, null=False)
    is_banned: bool = models.BooleanField(null=False, default=False)

    objects = MjUserManager()
