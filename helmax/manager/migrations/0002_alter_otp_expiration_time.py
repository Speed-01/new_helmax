# Generated by Django 5.1.4 on 2025-02-11 20:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 11, 20, 47, 43, 552649, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
