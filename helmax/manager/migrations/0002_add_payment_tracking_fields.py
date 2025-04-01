from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='last_payment_attempt',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]