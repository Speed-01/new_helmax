# Generated by Django 5.1.6 on 2025-03-18 04:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0036_alter_otp_expiration_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 18, 4, 24, 58, 976803, tzinfo=datetime.timezone.utc)),
        ),
    ]
