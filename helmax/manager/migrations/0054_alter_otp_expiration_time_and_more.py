# Generated by Django 5.1.6 on 2025-04-04 04:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0053_alter_otp_expiration_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 4, 4, 18, 51, 545511, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='returnrequest',
            name='admin_response',
            field=models.TextField(blank=True, null=True),
        ),
    ]
