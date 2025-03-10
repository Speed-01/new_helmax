# Generated by Django 5.1.4 on 2025-02-25 02:16

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0021_remove_returnrequest_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='admin_response',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='return_status',
            field=models.CharField(choices=[('NOT_REQUESTED', 'Not Requested'), ('PENDING', 'Return Requested'), ('APPROVED', 'Return Approved'), ('REJECTED', 'Return Rejected')], default='NOT_REQUESTED', max_length=20),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 25, 2, 16, 23, 46038, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='returnrequest',
            name='order_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_requests', to='manager.orderitem'),
        ),
        migrations.AlterField(
            model_name='returnrequest',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
