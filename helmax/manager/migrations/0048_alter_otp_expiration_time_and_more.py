# Generated by Django 5.1.6 on 2025-04-03 11:54

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0047_alter_otp_expiration_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 3, 11, 55, 29, 66385, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='wallettransaction',
            name='transaction_type',
            field=models.CharField(choices=[('CREDIT', 'Credit'), ('DEBIT', 'Debit'), ('REFUND', 'Refund'), ('RETURN_REFUND', 'Return Refund')], max_length=20),
        ),
    ]
