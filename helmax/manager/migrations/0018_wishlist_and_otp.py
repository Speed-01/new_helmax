from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('manager', '0017_cart_coupon_alter_otp_expiration_time'),  # This matches your last migration
    ]

    operations = [
        # First delete the wishlist model
        migrations.DeleteModel(
            name='Wishlist',
        ),
        
        # Then update OTP field
        migrations.AlterField(
            model_name='otp',
            name='expiration_time',
            field=models.DateTimeField(),
        ),
    ] 