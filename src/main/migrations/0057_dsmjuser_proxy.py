# Generated by Django 4.2.6 on 2023-12-10 12:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0056_stats"),
    ]

    operations = [
        migrations.AddField(
            model_name="dsmjuser",
            name="proxy",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Указывать только адрес без протокола",
                null=True,
                verbose_name="прокси",
            ),
        ),
    ]
