# Generated by Django 4.2.6 on 2023-11-04 14:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0033_blend_chat_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="pay",
            name="merchant",
            field=models.CharField(choices=[("YOOKASSA", "YOOKASSA"), ("WALLET", "WALLET")], null=True),
        ),
    ]
