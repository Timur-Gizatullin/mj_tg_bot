# Generated by Django 4.2.6 on 2023-12-09 09:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0055_messagenotify"),
    ]

    operations = [
        migrations.CreateModel(
            name="Stats",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action",
                    models.CharField(
                        choices=[("MJ_QUERY", "MJ_QUERY"), ("GPT_QUERY", "GPT_QUERY"), ("DALLE_QUERY", "DALLE_QUERY")],
                        default=None,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True, verbose_name="Время создания")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="stats",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
