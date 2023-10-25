from asgiref.sync import sync_to_async
from django.db import models


class DescribeManager(models.Manager):
    @sync_to_async
    def get_describe_by_file_name(self, file_name: str) -> "Describe":
        return self.filter(file_name=file_name).first()


class Describe(models.Model):
    file_name: str = models.CharField()
    chat_id: str = models.CharField()

    objects = DescribeManager()
