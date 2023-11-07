# Generated by Django 4.2.6 on 2023-11-06 22:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0045_user_invited_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="invited_by",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="invites",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пригласил",
            ),
        ),
    ]
