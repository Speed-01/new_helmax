# Generated by Django 5.1.4 on 2025-02-11 20:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0002_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 11, 20, 49, 12, 257706, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
