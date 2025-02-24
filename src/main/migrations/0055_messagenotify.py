# Generated by Django 4.2.6 on 2023-11-16 23:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0054_user_is_subscribed"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageNotify",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Можете указать название рассылки для удобства",
                        null=True,
                        verbose_name="Название сообщения",
                    ),
                ),
                (
                    "text",
                    models.TextField(
                        help_text="Введите сообщение для рассылки и укажите его id в задаче для рассылки",
                        verbose_name="Сообщение для рассылки",
                    ),
                ),
            ],
            options={
                "verbose_name": "Собщение для рассылки",
                "verbose_name_plural": "Сообщения для рассылки",
            },
        ),
    ]
