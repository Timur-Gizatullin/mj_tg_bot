# Generated by Django 4.2.6 on 2023-10-05 20:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_user_chat_id_user_generations_count_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="chat_id",
            field=models.IntegerField(null=True, unique=True),
        ),
    ]
