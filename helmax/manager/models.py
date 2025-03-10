from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.utils import timezone
from django.utils.timezone import now
from cloudinary.models import CloudinaryField
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
import random
from django.core.validators import RegexValidator
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
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
        self.expiration_time = self.created_at + timedelta(minutes=1)  # OTP expires in 1 minute
        self.save()

    def is_valid(self):
        return timezone.now() <= self.expiration_time

    def __str__(self):
        return f"OTP for {self.email}: {self.otp} (Expires at {self.expiration_time})"


    
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


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products',null=True, blank=True)
    is_active = models.BooleanField(default=True)  
    
    def __str__(self):
        return self.name

    def get_best_offer(self):
        now = timezone.now()
        
        # Check product offers
        product_offer = self.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-discount_percentage').first()
        
        # Check category offers
        category_offer = self.category.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-discount_percentage').first()
        
        # Return the better offer
        if product_offer and category_offer:
            return product_offer if product_offer.discount_percentage > category_offer.discount_percentage else category_offer
        return product_offer or category_offer

    def get_offer_price(self, original_price):
        offer = self.get_best_offer()
        if offer:
            discount = (offer.discount_percentage / 100) * original_price
            return original_price - discount
        return original_price


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
    
    @property
    def offer_price(self):
        return self.product.get_offer_price(self.price)

    @property
    def active_offer(self):
        return self.product.get_best_offer()

    @property
    def final_price(self):
        # Use offer price if available, otherwise use discount_price if set, or fall back to original price
        if self.active_offer:
            return self.offer_price
        return self.discount_price if self.discount_price else self.price

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
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_discount(self):
        # Product discounts (from variant discount_price)
        product_discount = sum(
            (item.variant.price - item.variant.discount_price) * item.quantity
            for item in self.items.all()
            if item.variant.discount_price
        )
        
        # Coupon discount
        coupon_discount = self.calculate_coupon_discount()
        
        return product_discount + coupon_discount
    
    def calculate_coupon_discount(self):
        if not self.coupon:
            return 0
            
        if self.coupon.type == 'percentage':
            return (self.total_price * self.coupon.value) / 100
        else:
            return min(self.coupon.value, self.total_price)  # Don't exceed cart total
    
    @property
    def final_price(self):
        return max(0, self.total_price - self.total_discount)

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
    def is_active(self):
       
        return (
            self.variant.is_active and
            self.variant.product.is_active and
            self.variant.product.category.is_active and
            self.variant.product.brand.is_active
        )
    
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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    variants = models.ManyToManyField(Variant)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

    @classmethod
    def get_or_create_wishlist(cls, user):
        wishlist, created = cls.objects.get_or_create(user=user)
        return wishlist



class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL , on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    referral_code = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.user.username
    

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


class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    
    REASON_CHOICES = [
        ('defective', 'Product Defective'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Item Not As Described'),
        ('size_issue', 'Size/Fit Issue'),
        ('other', 'Other')
    ]
    
    # Make order_item nullable initially
    order_item = models.ForeignKey('OrderItem', on_delete=models.CASCADE, related_name='return_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    admin_response = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Return request for {self.order_item}"


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
                order_item=data.get('order_item'),
                reason=data.get('reason'),
                description=data.get('description')
            )
            return JsonResponse({'success': True, 'message': 'Return request submitted'})
        return JsonResponse({'success': False, 'message': 'Cannot return this order'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'})

class Coupon(models.Model):
    COUPON_TYPES = (
        ('percentage', 'Percentage'),
        ('flat', 'Flat Amount')
    )
    
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=10, choices=COUPON_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    usage_limit = models.IntegerField()  # Per user usage limit
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code

class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('coupon', 'user', 'order')

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s wallet (₹{self.balance})"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('REFUND', 'Refund'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='SUCCESS')

    def __str__(self):
        return f"{self.transaction_type} of ₹{self.amount} for {self.wallet.user.username}"

class BaseOffer(models.Model):
    name = models.CharField(max_length=100)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def is_valid(self):
        now = timezone.now()
        return (self.is_active and 
                self.start_date <= now <= self.end_date)

class ProductOffer(BaseOffer):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    
    def __str__(self):
        return f"{self.name} - {self.product.name} ({self.discount_percentage}%)"

    class Meta:
        unique_together = ('product', 'start_date', 'end_date')

class CategoryOffer(BaseOffer):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='offers')
    
    def __str__(self):
        return f"{self.name} - {self.category.name} ({self.discount_percentage}%)"

    class Meta:
        unique_together = ('category', 'start_date', 'end_date')

class ReferralOffer(BaseOffer):
    referral_bonus = models.DecimalField(max_digits=10, decimal_places=2)
    referee_bonus = models.DecimalField(max_digits=10, decimal_places=2)
    usage_limit = models.IntegerField(default=1)  # How many times a user can refer
    
    def __str__(self):
        return f"{self.name} - Referral Offer"

class ReferralUsage(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referred_by')
    offer = models.ForeignKey(ReferralOffer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)  # Set to True after referee makes first purchase

    class Meta:
        unique_together = ('referrer', 'referee', 'offer')