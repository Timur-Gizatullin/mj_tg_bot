# Generated by Django 4.2.6 on 2023-10-13 18:40

from django.db import migrations
import main.models.user


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0009_discordqueue_telegram_user_user_role"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", main.models.user.UserManager()),
            ],
        ),
    ]
