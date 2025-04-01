from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0039_add_product_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_failure_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]