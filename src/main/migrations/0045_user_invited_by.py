# Generated by Django 4.2.6 on 2023-11-06 22:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0044_dsmjuser_fail_in_row_user_fail_in_row_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="invited_by",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="invites",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пригласил",
            ),
        ),
    ]
