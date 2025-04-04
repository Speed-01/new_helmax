# Generated by Django 5.1.4 on 2025-02-11 22:00

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0005_address_email_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="size",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="manager.size",
            ),
        ),
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 11, 22, 1, 28, 20310, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
