# Generated by Django 5.1.6 on 2025-06-07 16:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0002_alter_otp_expiration_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 6, 7, 16, 47, 54, 467280, tzinfo=datetime.timezone.utc)),
        ),
    ]
