# Generated by Django 4.2.6 on 2023-11-06 12:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0040_remove_user_telegram_user_id_alter_user_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="telegram_user_id",
            field=models.CharField(null=True, unique=True, verbose_name="ID телеграм пользоателя"),
        ),
    ]
