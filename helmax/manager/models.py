from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.timezone import now
from cloudinary.models import CloudinaryField
import datetime
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
import random
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User

from django.db import transaction
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver




from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
import re
from django.utils.crypto import get_random_string


class library(models.Model):
  
  
  image = CloudinaryField('image')

class User(AbstractUser):

    phone = models.CharField(max_length=15, blank=True, null=True, 
                              validators=[
                                  RegexValidator(
                                      regex=r'^\+?1?\d{9,15}$', 
                                      message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
                                  )
                              ])
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    referral_code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username or self.email
    
    def save(self, *args, **kwargs):
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self.generate_unique_referral_code()
        
        super().save(*args, **kwargs)

    def generate_unique_referral_code(self):
        # Generate a unique 8-character referral code
        while True:
            code = get_random_string(length=8).upper()
            if not User.objects.filter(referral_code=code).exists():
                return code


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expiration_time = models.DateTimeField(default=timezone.now() + timedelta(minutes=1))

    def generate_otp(self):
        self.otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.created_at = timezone.now()
        self.expiration_time = self.created_at + timedelta(minutes=1)

    def is_valid(self):
        return timezone.now() <= self.expiration_time

    def save(self, *args, **kwargs):
        if not self.expiration_time:
            self.expiration_time = self.created_at + timedelta(minutes=10)
        super().save(*args, **kwargs)


    
class BaseModel(models.Model):
    
    added_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True



class Category(BaseModel):
    name = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    

class Brand(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

from django.db import models
from django.core.exceptions import ValidationError






class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products',null=True, blank=True)
    is_active = models.BooleanField(default=True)  
    
    def __str__(self):
        return self.name


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True )
    is_active = models.BooleanField(default=True)
    
    def get_total_stock(self):
        return sum(size.stock for size in self.sizes.all())
    
    def is_in_stock(self):
        return self.get_total_stock() > 0
    
    def __str__(self):
        return f"{self.product.name} - {self.color}"
    
class Size(models.Model):
    SIZE_CHIOCES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    )
    name = models.CharField(max_length=10, choices=SIZE_CHIOCES)
    product_variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='sizes')
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product_variant} - {self.name}"


class ProductImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='images')  # Removed default
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.variant}"
    




    

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review for {self.product.name}"
    






########### Cart Models ####################

class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_ordered = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_discount(self):
        return sum(
            (item.variant.price - item.variant.discount_price) * item.quantity
            for item in self.items.all()
            if item.variant.discount_price
        )
    
    @property
    def final_price(self):
        return self.total_price - self.total_discount

class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=False, blank=False)
    quantity = models.PositiveIntegerField(default=1)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ('cart', 'variant', 'size')
    
    def __str__(self):
        return f"{self.quantity} x {self.variant} in {self.cart}"
    
    def sm():
        s = sum([quantity for quantity in CartItem])
        return s
    
    @property
    def subtotal(self):
        if self.variant.discount_price:
            return self.variant.discount_price * self.quantity
        return self.variant.price * self.quantity
    
    def clean(self):
        if not self.size:
            raise ValidationError("Size must be specified")
            
        if self.quantity > self.size.stock:
            raise ValidationError(f"Quantity cannot exceed available stock ({self.size.stock} available)")
            
        if self.quantity > 5:  # Maximum quantity per item
            raise ValidationError("Maximum quantity per item is 5")
    
    

    @property
    def subtotal(self):
        if self.variant.discount_price:
            return self.variant.discount_price * self.quantity
        return self.variant.price * self.quantity
    
    def clean(self):
        if self.quantity > self.variant.stock:
            raise ValidationError("Quantity cannot exceed available stock")
        if self.quantity > 5:  # Maximum quantity per item
            raise ValidationError("Maximum quantity per item is 5")
        

class Wishlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'variant')
    
    def __str__(self):
        return f"Wishlist item for {self.user.username}: {self.variant}"











class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name



##################                 ##################       
##################  Profile Models ##################                   
##################                 ##################


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL , on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    referral_code = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.user.username
    

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()

    ################# order models ####################


class Address(BaseModel):
    ADDRESS_TYPE_CHOICES = (
        ('HOME', 'Home'),
        ('WORK', 'Work'),
        ('OTHER', 'Other')
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_addresses')
    email = models.EmailField(null=True, blank=True)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]
    )
    pincode = models.CharField(
        max_length=6,
        validators=[RegexValidator(regex=r'^\d{6}$', message="Pincode must be 6 digits.")]
    )
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
      
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Use select_for_update to prevent race conditions
            with transaction.atomic():
                Address.objects.select_for_update().filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.address_type} address for {self.user.username}"

    class Meta:
        verbose_name_plural = "Addresses"


import uuid
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Order(BaseModel):
    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed')
    )
    
    ORDER_STATUS_CHOICES = (
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned')
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paymentmethod = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, default=1)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PROCESSING')
   
    
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100 , null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

    
    

class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE , null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=[
        ("Pending", "Pending"), 
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Returned", "Returned"),
        ("Refunded", "Refunded"),
        ("Failed", "Failed"),
        ('Shipped','Shipped'),
        ('Out of Delivery','Out of Delivery'),
        ('Processing',"Processing"),
        ('Approved','Approved'),
        ('Rejected','Rejected'),
        
    ], default="Shipped")
    cancellation_reason = models.TextField(null=True,blank=True)
    return_reason = models.TextField(null=True,blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return self.price * self.quantity
    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order: {self.order.id})"


# class ReturnRequest(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#     ]

#     order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='return_request')
#     reason = models.TextField()
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     admin_response = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"Return Request for Order {self.order.id}"

# models.py
from django.db import models

class ReturnRequest(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    
    RETURN_REASON_CHOICES = [
        ('size_issue', 'Size Issue'),
        ('product_defect', 'Product Defect'),
        ('wrong_item', 'Wrong Item Received'),
        ('other', 'Other')
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    reason = models.CharField(max_length=50, choices=RETURN_REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

@login_required
@require_POST
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        if order.order_status == 'PROCESSING':
            order.order_status = 'CANCELLED'
            order.save()
            return JsonResponse({'success': True, 'message': 'Order cancelled successfully'})
        return JsonResponse({'success': False, 'message': 'Cannot cancel this order'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'})

@login_required
@require_POST
def create_return_request(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        if order.order_status == 'DELIVERED':
            data = json.loads(request.body)
            return_request = ReturnRequest.objects.create(
                order=order,
                reason=data.get('reason'),
                description=data.get('description')
            )
            return JsonResponse({'success': True, 'message': 'Return request submitted'})
        return JsonResponse({'success': False, 'message': 'Cannot return this order'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'})