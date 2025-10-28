from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from manager.models import (
    User, Product, Variant, Size, Cart, CartItem, Address, Coupon, Category, Brand
)


class DeliveryChargeTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass12345'
        )

        # Create a category and a product/variant/size
        self.category = Category.objects.create(name='TestCat')
        self.product = Product.objects.create(name='Test Product', description='desc', category=self.category)

        # Ensure product has a brand (some checks assume brand exists)
        self.brand = Brand.objects.create(name='TestBrand')
        self.product.brand = self.brand
        self.product.save()

        self.variant = Variant.objects.create(product=self.product, price=Decimal('100.00'))
        self.size = Size.objects.create(name='M', product_variant=self.variant, stock=10)

        # Create a cart and add an item
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=2, size=self.size)

        # Create a default address for checkout
        self.address = Address.objects.create(
            user=self.user,
            address_type='HOME',
            full_name='Test User',
            phone='+911234567890',
            pincode='560001',
            address_line1='Line 1',
            city='Bengaluru',
            state='Karnataka'
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_get_cart_totals_returns_delivery_zero(self):
        url = reverse('get_cart_totals')
        resp = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        # delivery_charge should be present and zero
        self.assertAlmostEqual(float(data.get('delivery_charge', 0)), 0.0, places=2)

    def test_checkout_view_context_has_delivery_zero(self):
        url = reverse('user_checkout')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Django TestResponse exposes context
        delivery = float(resp.context['delivery_charge'])
        self.assertAlmostEqual(delivery, 0.0, places=2)

    def test_apply_coupon_response_contains_delivery_zero(self):
        # Create a coupon that applies
        import datetime
        today = datetime.date.today()
        coupon = Coupon.objects.create(
            code='TEST10', type='flat', value=Decimal('10.00'), minimum_purchase=Decimal('0.00'),
            is_active=True, start_date=today, end_date=today.replace(year=today.year + 1), usage_limit=10
        )

        # Use explicit store path to avoid name collisions with manager's apply_coupon
        url = '/cart/apply-coupon/'
        resp = self.client.post(url, data=json.dumps({'code': 'TEST10'}), content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertAlmostEqual(float(data.get('delivery_charge', 0)), 0.0, places=2)
