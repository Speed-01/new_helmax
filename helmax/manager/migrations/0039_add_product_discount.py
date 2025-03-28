from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('manager', '0038_merge_20250324_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='product_discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]