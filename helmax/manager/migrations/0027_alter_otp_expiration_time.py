# Generated by Django 5.1.6 on 2025-03-14 08:04

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0026_alter_otp_expiration_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 14, 8, 5, 27, 948126, tzinfo=datetime.timezone.utc)),
        ),
    ]
