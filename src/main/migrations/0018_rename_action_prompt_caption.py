# Generated by Django 4.2.6 on 2023-10-19 00:05

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0017_remove_prompt_parent_id_prompt_action"),
    ]

    operations = [
        migrations.RenameField(
            model_name="prompt",
            old_name="action",
            new_name="caption",
        ),
    ]
