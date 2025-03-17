from django.db import migrations, models
from django.utils import timezone

class Migration(migrations.Migration):
    dependencies = [
        ('manager', '0029_rename_updated_date_order_updated_at_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE manager_order 
            SET order_number = CONCAT('ORD', LPAD(CAST(id AS VARCHAR), 8, '0'))
            WHERE order_number IS NULL OR order_number = 'OLD_ORDER';
            """
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(default=timezone.now() + timezone.timedelta(days=365)),
        )
    ]