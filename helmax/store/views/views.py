from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib import messages
from django.utils.timezone import now
from manager.forms import SignupForm, OTPVerificationForm, PasswordResetRequestForm, SetPasswordForm
from ..forms import AddressForm
from django.http import Http404
from django.conf import settings
import os
from ..invoice_generator import generate_invoice_pdf
from manager.models import (
    OTP, User, Category, Brand, Size, Product, Variant, ProductImage,
    Review, Address, Cart, CartItem, PaymentMethod, Coupon, CouponUsage,
    Order, OrderItem, Wishlist, ReturnRequest, Wallet, WalletTransaction
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

def home(request):
    return render(request, 'home.html')