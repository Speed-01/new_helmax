# Generated by Django 5.1.4 on 2025-02-13 02:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0009_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 13, 2, 26, 21, 744750, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
