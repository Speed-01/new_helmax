# Generated by Django 5.1.4 on 2025-02-11 20:59

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0003_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 11, 21, 0, 14, 825679, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
