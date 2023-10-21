from django.db import models


class MjUserManager(models.Manager):
    def get_mj_users(self) -> list["MjUser"]:
        return self.filter(is_banned=False).all()


class MjUser(models.Model):
    token: str = models.CharField(unique=True, null=False)
    is_banned: bool = models.BooleanField(null=False, default=False)

    objects = MjUserManager()
