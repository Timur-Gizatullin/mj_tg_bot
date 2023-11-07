# Generated by Django 4.2.6 on 2023-11-07 19:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import main.enums


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0043_dsmjuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="dsmjuser",
            name="fail_in_row",
            field=models.IntegerField(default=0, verbose_name="Ошибок подряд"),
        ),
        migrations.AddField(
            model_name="user",
            name="fail_in_row",
            field=models.IntegerField(default=0, verbose_name="Ошибок подряд"),
        ),
        migrations.AddField(
            model_name="user",
            name="gen_date",
            field=models.DateTimeField(auto_now=True, null=True, verbose_name="Дата последней генерации"),
        ),
        migrations.AddField(
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
        migrations.AddField(
            model_name="user",
            name="pay_date",
            field=models.DateTimeField(null=True, verbose_name="Дата последней оплаты"),
        ),
        migrations.AlterField(
            model_name="user",
            name="state",
            field=models.CharField(
                choices=[("PENDING", "PENDING"), ("READY", "READY"), ("BANNED", "BANNED")],
                default=main.enums.UserStateEnum["READY"],
                verbose_name="Состояние",
            ),
        ),
    ]
