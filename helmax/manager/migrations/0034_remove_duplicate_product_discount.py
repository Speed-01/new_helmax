from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('manager', '0033_alter_order_payment_method_alter_otp_expiration_time'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Remove the duplicate product_discount field
            ALTER TABLE manager_order DROP COLUMN IF EXISTS product_discount;
            """
        ),
    ]