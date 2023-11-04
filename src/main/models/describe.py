from asgiref.sync import sync_to_async
from django.db import models


class DescribeManager(models.Manager):
    @sync_to_async
    def get_describe_by_file_name(self, file_name: str) -> "Describe":
        return self.filter(file_name=file_name).first()


class Describe(models.Model):
    file_name: str = models.CharField()
    chat_id: str = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = DescribeManager()

    def __str__(self):
        return f"{self.chat_id}[{self.created_at}]"