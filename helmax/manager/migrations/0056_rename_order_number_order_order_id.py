from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('manager', '0055_fix_returnrequest_admin_response'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='order_number',
            new_name='order_id',
        ),
    ]