# Generated by Django 4.2.6 on 2023-11-05 23:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0035_price_alter_banword_options_alter_blend_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(null=True),
        ),
    ]
