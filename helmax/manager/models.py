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
from django.utils.text import slugify
from decimal import Decimal

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
    expiration_time = models.DateTimeField(null=True, blank=True)

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
        
        # Get all active product offers
        product_offers = self.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-discount_percentage')
        
        # Get all active category offers
        category_offers = self.category.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-discount_percentage')
        
        # Combine all offers and sort by discount percentage
        all_offers = list(product_offers) + list(category_offers)
        if not all_offers:
            return None
            
        # Return the offer with highest discount percentage
        return max(all_offers, key=lambda x: x.discount_percentage)

    def get_offer_price(self, original_price):
        offer = self.get_best_offer()
        if offer:
            discount = (offer.discount_percentage / 100) * original_price
            return original_price - discount
        return original_price
    
    def get_average_rating(self):
        """Calculate average rating for this product"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return 0
    
    def get_rating_distribution(self):
        """Get count of reviews for each star rating"""
        reviews = self.reviews.filter(is_approved=True)
        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for review in reviews:
            distribution[review.rating] += 1
        return distribution
    
    def get_total_reviews(self):
        """Get total number of approved reviews"""
        return self.reviews.filter(is_approved=True).count()


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


    @property
    def url(self):
        """Get image URL with fallback to default if image is invalid"""
        try:
            return self.image.url
        except Exception:
            # Return None so the template can handle fallback
            return None
    
    def save(self, *args, **kwargs):
        # If this is marked as primary, unset primary flag for other images of this variant
        if self.is_primary:
            ProductImage.objects.filter(variant=self.variant).update(is_primary=False)
        super().save(*args, **kwargs)
        
        # If this is the only image for the variant, make it primary
        if not self.is_primary and not ProductImage.objects.filter(variant=self.variant, is_primary=True).exists():
            self.is_primary = True
            super().save(update_fields=['is_primary'])


########### Cart Models ####################

from decimal import Decimal
from django.core.exceptions import ValidationError

class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_ordered = models.BooleanField(default=False)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_price(self):
        """Calculate total price of active items only."""
        total = Decimal('0.00')
        for item in self.items.all():
            try:
                price = Decimal(str(item.variant.final_price or item.variant.price))
                total += price * item.quantity
            except (TypeError, ValueError):
                continue  # Skip items with invalid prices
        return total.quantize(Decimal('0.01'))
    
    @property
    def total_discount(self):
        """Calculate total discount including product and coupon discounts."""
        product_discount = Decimal('0.00')
        for item in self.items.all():
            try:
                if item.variant.discount_price and item.variant.price:
                    discount = Decimal(str(item.variant.price - item.variant.discount_price)) * item.quantity
                    product_discount += discount
            except (TypeError, ValueError):
                continue
        
        coupon_discount = self.calculate_coupon_discount()
        return (product_discount + coupon_discount).quantize(Decimal('0.01'))
    
    def calculate_coupon_discount(self):
        """Calculate coupon discount if applicable."""
        if not self.coupon:
            return Decimal('0.00')
        
        # Validate coupon is active
        if not self.coupon.is_active:
            self.coupon = None
            self.save()
            return Decimal('0.00')
        
        # Validate coupon date range
        today = timezone.now().date()
        if self.coupon.start_date > today or self.coupon.end_date < today:
            self.coupon = None
            self.save()
            return Decimal('0.00')
        
        # Validate minimum purchase requirement
        cart_total = self.total_price
        min_purchase = Decimal(str(self.coupon.minimum_purchase))
        if cart_total < min_purchase:
            # Don't remove the coupon, just return 0 discount
            # This allows the frontend to show appropriate messages
            return Decimal('0.00')
        
        # Calculate discount based on coupon type
        if self.coupon.type == 'percentage':
            discount = (cart_total * Decimal(str(self.coupon.value))) / Decimal('100')
        else:  # flat amount
            discount = Decimal(str(self.coupon.value))
        
        # Ensure discount doesn't exceed cart total
        return min(discount, cart_total).quantize(Decimal('0.01'))
    
    @property
    def final_price(self):
        """Calculate final price after coupon discount (product discounts already in total_price)."""
        coupon_discount = self.calculate_coupon_discount()
        return max(Decimal('0.00'), self.total_price - coupon_discount).quantize(Decimal('0.01'))
    
    def update_totals(self):
        """Update cart totals and validate items."""
        with transaction.atomic():
            self.refresh_from_db()
            for item in self.items.all():
                if not item.is_active or item.quantity > item.size.stock:
                    item.delete()  # Remove invalid items
            self.save()  # Save to trigger any signal handlers
            
class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=False, blank=False)
    quantity = models.PositiveIntegerField(default=1)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ('cart', 'variant', 'size')
    
    def __str__(self):
        return f"{self.quantity} x {self.variant} in {self.cart}"
    
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
        price = Decimal(str(self.variant.final_price or self.variant.price))
        return (price * self.quantity).quantize(Decimal('0.01'))
    
    def clean(self):
        if not self.size:
            raise ValidationError("Size must be specified")
        
        if self.quantity > self.size.stock:
            raise ValidationError(f"Quantity cannot exceed available stock ({self.size.stock} available)")
        
        if self.quantity > 5:
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


class OrderStatusHistory(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    reason = models.TextField(blank=True, null=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order.order_id}: {self.old_status} -> {self.new_status}'

class Order(BaseModel):
    product_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    ORDER_STATUSES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned')
    ]
    
    @property
    def calculated_product_discount(self):
        """Calculate product discount from order items (for old orders or verification)"""
        return sum(item.total_discount for item in self.order_items.all())
    
    @property
    def total_discount(self):
        # Use stored discount if available, otherwise calculate from items
        product_disc = self.product_discount if self.product_discount > 0 else self.calculated_product_discount
        return product_disc + self.coupon_discount
    
    @property
    def actual_paid_amount(self):
        """Calculate the actual amount paid (subtotal - all discounts)"""
        product_disc = self.product_discount if self.product_discount > 0 else self.calculated_product_discount
        return max(0, self.subtotal - product_disc - self.coupon_discount)
    
    @property
    def final_price(self):
        return max(0, self.total_amount - self.total_discount)
        
    @property
    def subtotal(self):
        # Calculate subtotal from original prices (MRP)
        return sum(
            item.total_original_price if item.original_price > 0 else item.total_price
            for item in self.order_items.all()
        )
    
    PAYMENT_STATUSES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('PAYMENT_PENDING', 'Payment Pending'),
        ('REFUNDED', 'Refunded')
    ]
    
    payment_attempts = models.IntegerField(default=0)
    last_payment_attempt = models.DateTimeField(null=True, blank=True)
    payment_failure_reason = models.TextField(blank=True, null=True)
    payment_expiry_time = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=25, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=30, choices=ORDER_STATUSES, default='PENDING')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUSES, default='PENDING')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='orders')
    
    # Status timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Address fields
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address_line1 = models.CharField(max_length=100, null=True, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    
    # Tracking
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    shipping_carrier = models.CharField(max_length=50, blank=True, null=True)
    
    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            # Generate a unique order ID based on timestamp and random string
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_suffix = get_random_string(4).upper()
            self.order_id = f'ORD{timestamp}-{random_suffix}'
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    ITEM_STATUSES = [
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned')
    ]
    
    RETURN_STATUSES = [
        ('NOT_REQUESTED', 'Not Requested'),
        ('REQUESTED', 'Return Requested'),
        ('APPROVED', 'Return Approved'),
        ('REJECTED', 'Return Rejected'),
        ('IN_TRANSIT', 'Return in Transit'),
        ('COMPLETED', 'Return Completed')
    ]
    
    RETURN_REASONS = [
        ('DEFECTIVE', 'Product Defective'),
        ('WRONG_ITEM', 'Wrong Item Received'),
        ('NOT_AS_DESCRIBED', 'Item Not As Described'),
        ('SIZE_ISSUE', 'Size/Fit Issue'),
        ('OTHER', 'Other')
    ]

    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price customer paid (after discount)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # MRP before discount
    
    status = models.CharField(max_length=20, choices=ITEM_STATUSES, default='PROCESSING')
    return_status = models.CharField(max_length=20, choices=RETURN_STATUSES, default='NOT_REQUESTED')
    
    # Timestamps for item status changes
    confirmed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True) 
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    @property
    def item_discount(self):
        """Discount per unit"""
        return self.original_price - self.price if self.original_price > 0 else 0
    
    @property
    def total_original_price(self):
        """Total MRP for this item"""
        return self.original_price * self.quantity
    
    @property
    def total_price(self):
        """Total price customer pays for this item"""
        return self.price * self.quantity
    
    @property
    def total_discount(self):
        """Total discount for this item (product discount only, not coupon)"""
        return self.item_discount * self.quantity
    
    def get_refundable_amount(self):
        """
        Calculate the actual refundable amount for this item based on what customer ACTUALLY PAID.
        
        Logic:
        1. Calculate ORIGINAL order total (sum of all items before any cancellations/returns)
        2. Calculate this item's proportion of the original order
        3. Apply proportion to ORIGINAL order.total_amount to get this item's share
        
        Example:
        Original Order (3 items):
        - Item A: ₹3897
        - Item B: ₹1000  
        - Item C: ₹500
        - Total before coupon: ₹5397
        - Coupon: -₹539.70
        - Customer paid: ₹4857.30
        
        Item A proportion: 3897/5397 = 72.2%
        Item A refund: 72.2% × ₹4857.30 = ₹3,507.00
        
        Even if Item B is already cancelled, Item A's refund stays ₹3,507.00
        """
        # Get all order items (ALL items, including cancelled/returned)
        all_items = self.order.order_items.all()
        
        # Calculate ORIGINAL total before coupon (sum of ALL item prices)
        original_total_before_coupon = sum(
            Decimal(str(item.price)) * item.quantity for item in all_items
        )
        
        if original_total_before_coupon <= 0:
            return Decimal('0')
        
        # Calculate this item's price (after product discount, before coupon)
        item_price = Decimal(str(self.price)) * self.quantity
        
        # Calculate this item's proportion of the ORIGINAL order
        item_proportion = item_price / original_total_before_coupon
        
        # Calculate ORIGINAL amount customer paid (before any refunds)
        # This is: original_total_before_coupon - original_coupon_discount
        original_coupon = Decimal(str(self.order.coupon_discount)) if self.order.coupon_discount else Decimal('0')
        original_paid = original_total_before_coupon - original_coupon
        
        # Calculate refund as proportion of ORIGINAL paid amount
        refundable = item_proportion * original_paid
        
        return refundable.quantize(Decimal('0.01'))

    def can_return(self):
        if self.status != 'DELIVERED':
            return False
        if not self.delivered_at:
            return False
        return_deadline = self.delivered_at + timezone.timedelta(days=7)
        return timezone.now() <= return_deadline
        
    def __str__(self):
        product_name = self.product.name if self.product else 'Unknown Product'
        variant_info = f" - {self.variant.color}" if self.variant and self.variant.color else ''
        size_info = f" - {self.size.name}" if self.size else ''
        return f"{product_name}{variant_info}{size_info} (Order: {self.order.order_id})"

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
    
    # Make order_item nullable to handle cases where the order item might not exist
    order_item = models.ForeignKey('OrderItem', on_delete=models.CASCADE, related_name='return_requests', null=True, blank=True)
    admin_response = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
      
    
    def __str__(self):
        if self.order_item:
            return f"Return request for {self.order_item}"
        return f"Return request #{self.id} by {self.user.username if self.user else 'Unknown user'}"

class AdminResponse(models.Model):
    RESPONSE_TYPES = (
        ('INFO', 'Information'),
        ('STATUS_UPDATE', 'Status Update'),
        ('RETURN', 'Return Response'),
        ('CANCELLATION', 'Cancellation Response'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='admin_responses')
    message = models.TextField()
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

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
        ('RETURN_REFUND', 'Return Refund'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
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

    def save(self, *args, **kwargs):
        # Ensure datetime fields are timezone-aware
        if self.start_date and timezone.is_naive(self.start_date):
            self.start_date = timezone.make_aware(self.start_date)
        if self.end_date and timezone.is_naive(self.end_date):
            self.end_date = timezone.make_aware(self.end_date)
        super().save(*args, **kwargs)

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


class Review(models.Model):
    """
    Product reviews with ratings
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='review')
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    comment = models.TextField()
    
    # Review status
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)  # For moderation
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Helpful votes
    helpful_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user', 'order_item')  # One review per purchase
        indexes = [
            models.Index(fields=['product', 'is_approved', '-created_at']),
            models.Index(fields=['product', 'is_approved', '-helpful_count']),
            models.Index(fields=['product', 'is_approved', 'rating']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


class ReviewImage(models.Model):
    """
    Images attached to reviews
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('review_image')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for review #{self.review.id}"


class ReviewHelpful(models.Model):
    """
    Track which users found reviews helpful
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
    
    def __str__(self):
        return f"{self.user.username} found review #{self.review.id} helpful"