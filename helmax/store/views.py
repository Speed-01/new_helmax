from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate,logout as auth_logout
from django.contrib import messages
from django.utils.timezone import now
from manager.forms import SignupForm, OTPVerificationForm, PasswordResetRequestForm,SetPasswordForm
from .forms import AddressForm
from manager.models import OTP,User,Category, Brand, Size, Product, Variant, ProductImage, Review, Address, Cart, CartItem,PaymentMethod, Coupon, CouponUsage, Wishlist, ReturnRequest, Wallet, WalletTransaction,OrderStatusHistory
from datetime import timezone
from django.views.decorators.cache import never_cache
from django.http import  JsonResponse
from manager.models import (
    OTP, User, Category, Brand, Size, Product, Variant, ProductImage,   
    Review, Address, Cart, CartItem, Coupon, CouponUsage, PaymentMethod,
    Order, OrderItem, Wishlist, ReturnRequest, Wallet, WalletTransaction
)
import os
from django.http import Http404
from decimal import Decimal
import random 

PAYMENT_METHODS = [
    {'id': 'razorpay', 'name': 'Razorpay', 'description': 'Pay using Credit/Debit Card, UPI, or Net Banking'},
    {'id': 'cod', 'name': 'Cash on Delivery', 'description': 'Pay when your order is delivered'}
]
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import  JsonResponse, HttpResponse
import json
from django.conf import settings
from django.apps import apps
from .utils import send_otp_email
from .invoice_generator import generate_invoice_pdf
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import logging  
from django.db.models import Sum, F, Count, Min, Max, Avg, FloatField, ExpressionWrapper
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Prefetch
from django.urls import reverse   
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import logging
import re
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render, redirect
from django.contrib import messages
import logging
import razorpay

logger = logging.getLogger(__name__)
def home(request):
    # Get active categories and brands
    categories = Category.objects.filter(is_active=True).only('id', 'name')
    brands = Brand.objects.filter(is_active=True).only('id', 'name')

    # Prefetch variants and related data
    active_variants = Variant.objects.filter(is_active=True).select_related('product').prefetch_related('images', 'sizes').annotate(
        stock_total=Sum('sizes__stock')
    )

    products = (
        Product.objects.filter(is_active=True)
        .select_related('category', 'brand')
        .prefetch_related(Prefetch('variants', queryset=active_variants))
        .annotate(
            total_stock=Sum('variants__sizes__stock'),
            has_active_variants=Count('variants', filter=Q(variants__is_active=True))
        )
        .filter(has_active_variants__gt=0)
    )[:10]

    # Prepare simplified product data for the template
    product_data = []
    for product in products:
        first_variant = product.variants.filter(is_active=True).first()
        if not first_variant:
            continue

        # Get primary image or fallback
        primary_image = first_variant.images.filter(is_primary=True).first() or first_variant.images.first()

        # Safely get image URL
        image_url = None
        if primary_image and primary_image.image:
            try:
                image_url = primary_image.image.url
            except (ValueError, AttributeError):
                image_url = None

        product_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(first_variant.price),
            'discount_price': float(first_variant.discount_price) if first_variant.discount_price else None,
            'image_url': image_url,  # Let template handle missing images
            'category': product.category.name if product.category else '',
            'brand': product.brand.name if product.brand else '',
        })

    # Prepare filter options
    filter_data = {
        'categories': [{'id': cat.id, 'name': cat.name} for cat in categories],
        'brands': [{'id': brand.id, 'name': brand.name} for brand in brands],
        'price_range': {
            'min': products.aggregate(min_price=Min('variants__price'))['min_price'] or 0,
            'max': products.aggregate(max_price=Max('variants__price'))['max_price'] or 0
        },
        'sort_options': [
            {'value': 'newest', 'label': 'Newest First'},
            {'value': 'price_low_high', 'label': 'Price: Low to High'},
            {'value': 'price_high_low', 'label': 'Price: High to Low'},
            {'value': 'name_asc', 'label': 'Name: A to Z'},
            {'value': 'name_desc', 'label': 'Name: Z to A'},
            {'value': 'popularity', 'label': 'Most Popular'}
        ]
    }

    context = {
        'products': product_data,
        'filters': filter_data
    }
    return render(request, 'home.html', context)


def signup(request):
    form_data = {}
    if request.method == 'POST':
        form = SignupForm(request.POST)
        # Store form data for re-rendering
        form_data = {
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'email': request.POST.get('email', ''),
            'phone': request.POST.get('phone', '')
        }
        
        if form.is_valid():
            signup_data = form.cleaned_data
            request.session['signup_data'] = signup_data

            otp_instance, created = OTP.objects.get_or_create(email=signup_data['email'])
            otp_instance.generate_otp()
            otp_instance.save()
            print(otp_instance.otp)  
            try:
                send_otp_email(signup_data['email'], otp_instance.otp, purpose="signup")
                request.session['otp_timer_start'] = now().timestamp()
                
                messages.success(request, "Please verify your email with the OTP.")
            
                return redirect('verify_otp')
            except Exception as e:
                messages.error(request, f"Failed to send OTP. Please try again. Error: {str(e)}")
                return render(request, 'signup.html', {'form': form, 'form_data': form_data})
        else:
            for field, errors in form.errors.items():
                field_name = field.replace('_', ' ').title()
                for error in errors:
                    messages.error(request, f"{field_name}: {error}")
            return render(request, 'signup.html', {'form': form, 'form_data': form_data})
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form, 'form_data': form_data})





def verify_otp(request):
    print("verify_otp.......//")
    signup_data = request.session.get('signup_data')
    print("signup_data", signup_data)
    if not signup_data:
        messages.error(request, 'Session expired or invalid. Please sign up again.')
        return redirect('signup')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            try:
                otp_instance = OTP.objects.get(email=signup_data['email'])
                
                if not otp_instance.is_valid():
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': 0})

                if otp_instance.otp != entered_otp:
                    messages.error(request, 'Invalid OTP. Please try again.')
                    time_remaining = max(0, int((otp_instance.expiration_time - timezone.now()).total_seconds()))
                    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': time_remaining})

                try:
                    print("inside try")
                    print("signup_data['email']", signup_data['email'])
                    user = User.objects.create_user(
                        username=signup_data['first_name'],
                        email=signup_data['email'],
                        phone=signup_data['phone'],
                        password=signup_data['password1'],
                        first_name=signup_data.get('first_name', ''),
                        last_name=signup_data.get('last_name', ''),
                    )
                    print("user is created")
                    print("the user.......", user)
                    
                    request.session.pop('signup_data', None)
                    otp_instance.delete()

                    messages.success(request, 'Account created successfully! Please log in.')
                    return redirect('home')

                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
                    return redirect('signup')

            except OTP.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Unable to process your request. Please try signing up again.'})
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = OTPVerificationForm()

    try:
        otp_instance = OTP.objects.get(email=signup_data['email'])
        time_remaining = max(0, int((otp_instance.expiration_time - timezone.now()).total_seconds()))
    except OTP.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Unable to process your request. Please try signing up again.'})

    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': time_remaining})


# @csrf_exempt
# def login(request):
#                 messages.error(request, 'Invalid session. Please try again.')
#                 return redirect('signup')
#         else:
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, f"{field.capitalize()}: {error}")
#         else:
#             form = OTPVerificationForm()

#         try:
#         otp_instance = OTP.objects.get(email=signup_data['email'])
#         time_remaining = max(0, int((otp_instance.expiration_time - timezone.now()).total_seconds()))
#     except OTP.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Unable to process your request. Please try signing up again.'})

#     @csrf_exempt
#     def login(request):
#         time_remaining = 0

#     return render(request, 'verify_otp.html', {'form': form, 'time_remaining': time_remaining})



# def send_otp_email(email, otp):
#     subject = "Your OTP for Signup"
#     message = f"Your OTP is {otp}. It is valid for 10 minutes."
#     # Implement your email sending logic here
#     print(f"Sending OTP email to {email}: {message}")  # For development purposes

@require_http_methods(["POST"])
def resend_otp(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        return JsonResponse({'success': False, 'message': 'Invalid session. Please sign up again.'})

    try:
        otp_instance = OTP.objects.get(email=signup_data['email'])
        
        
        if timezone.now() < otp_instance.created_at + timezone.timedelta(seconds=60):
            time_to_wait = 60 - int((timezone.now() - otp_instance.created_at).total_seconds())
            return JsonResponse({'success': False, 'message': f'Please wait {time_to_wait} seconds before requesting a new OTP.'})

        otp_instance.generate_otp()
        otp_instance.save()

        try:
            send_otp_email(signup_data['email'], otp_instance.otp)
            return JsonResponse({'success': True, 'message': 'A new OTP has been sent to your email.'})
        except Exception as e:
            
            print(f"Payment verification failed with error: {str(e)}")

            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
    
    except OTP.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Unable to process your request. Please try signing up again.'})

    # 





@csrf_exempt
def login(request):
    if request.session.get('signup_success'):
        messages.success(request, "Your account was created successfully! Please log in.")
        del request.session['signup_success']
        print("signup_success")  
    
    email_value = ''
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        email_value = email  # Store for re-rendering
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            # Check if user is admin/staff
            if user.is_staff or user.is_superuser:
                messages.error(request, "Admin users should use the admin login page.")
                return render(request, 'login.html', {'email': email_value})
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'login.html', {'email': email_value})

    if request.user.is_authenticated:
        # Check if authenticated user is admin/staff
        if request.user.is_staff or request.user.is_superuser:
            messages.error(request, "Admin users should use the admin login page.")
            return redirect('adminLogin')
        return redirect('home')
    
    return render(request, 'login.html', {'email': email_value})



User = get_user_model()
logger = logging.getLogger(__name__)

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            validate_email(email)
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "No account found with this email.")
                return render(request, 'forgot_password.html')
            
            otp_instance, created = OTP.objects.get_or_create(email=email)
            otp_instance.generate_otp()
            otp_instance.save()

            logger.info(f"OTP generated for {email}: {otp_instance.otp}")
            
            try:
                send_otp_email(email, otp_instance.otp)
                request.session['reset_email'] = email
                messages.success(request, "OTP sent to your email.")
                return redirect('reset_password')
            except Exception as e:
                logger.error(f"Failed to send OTP email to {email}: {e}")   
                messages.error(request, "Failed to send OTP email. Please try again.")
        except ValidationError:
            messages.error(request, "Invalid email address.")
        except Exception as e:
            logger.error(f"Error in forgot_password view: {e}")
            messages.error(request, "An error occurred. Please try again.")
            
    return render(request, 'forgot_password.html')

def reset_password(request):
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, "Please submit your email first.")
        return redirect('forgot_password')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        try:
            otp_instance = OTP.objects.get(email=reset_email)
            if otp_instance.is_valid() and otp_instance.otp == otp:
                if new_password == confirm_password:
                    # Regex validation for password
                    if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*]).{8,}$', new_password):
                        messages.error(request, "Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one number, and one special character.")
                        return render(request, 'reset_password.html')
                    
                    try:
                        validate_password(new_password)
                        user = User.objects.get(email=reset_email)
                        user.set_password(new_password)
                        user.save()
                        
                        del request.session['reset_email']
                        otp_instance.delete()
                        
                        messages.success(request, "Password has been reset successfully!")
                        return redirect('Login')
                    except ValidationError as e:
                        messages.error(request, e.messages[0])
                else:
                    messages.error(request, "Passwords do not match.")
            else:
                messages.error(request, "Invalid or expired OTP.")
        except (OTP.DoesNotExist, User.DoesNotExist):
            messages.error(request, "Invalid reset attempt.")
    
    return render(request, 'reset_password.html')




def logout(request):
    auth_logout(request)
    return redirect('Login')

def confirm_logout(request):
    if request.method == 'POST':
        auth_logout(request)
        return redirect('Login')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def prepare_product_data(products):
    product_data = []
    for product in products:
        # Get first active variant
        first_variant = product.variants.filter(is_active=True).first()
        if first_variant:
            # Get primary image or first image
            primary_image = first_variant.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = first_variant.images.first()

            # Calculate total stock
            total_stock = sum(
                size.stock 
                for variant in product.variants.all() 
                for size in variant.sizes.all()
            )

            # Calculate discount percentage
            discount_percentage = None
            if first_variant.discount_price and first_variant.price:
                discount_percentage = int(
                    ((first_variant.price - first_variant.discount_price) / first_variant.price) * 100
                )

            product_data.append({
                'id': product.id,
                'name': product.name,
                'price': first_variant.price,
                'discount_price': first_variant.discount_price or first_variant.price,
                'image_url': primary_image.image.url if primary_image else None,
                'total_stock': total_stock,
                'discount_percentage': discount_percentage,
                'category': product.category.name,
                'brand': product.brand.name if product.brand else None,
            })
    return product_data

def product_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query),
        is_active=True
    ).prefetch_related('variants')

    product_data = []
    for product in products:
        variant = product.variants.first()
        product_data.append({
            'id': product.id,
            'name': product.name,
            'price': variant.price,
            'image_url': variant.images.first().image.url if variant.images.exists() else '',
            'description': product.description[:100]
        })

    return render(request, 'product_list.html', {'products': product_data})

def filter_products(request):
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True
    ).distinct()
    
    # Category filter
    categories = request.GET.get('categories', '').split(',')
    if categories and categories[0]:
        products = products.filter(category_id__in=categories)
    
    # Brand filter
    brands = request.GET.get('brands', '').split(',')
    if brands and brands[0]:
        products = products.filter(brand_id__in=brands)
    
    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        try:
            min_price = float(min_price)
            max_price = float(max_price)
            products = products.filter(
                variants__price__gte=min_price,
                variants__price__lte=max_price
            ).distinct()
        except (ValueError, TypeError):
            # If price conversion fails, ignore price filter
            pass
    
    # Search filter
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Sorting
    sort = request.GET.get('sort', 'new_arrivals')
    if sort == 'price_low_high':
        products = products.order_by('variants__price')
    elif sort == 'price_high_low':
        products = products.order_by('-variants__price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    else:
        # Default sorting by newest
        products = products.order_by('-id')
    
    # Prepare product data
    product_data = []
    for product in products:
        # Get first active variant
        first_variant = product.variants.filter(is_active=True).first()
        if not first_variant:
            continue  # Skip products without active variants
            
        # Get primary image or first image
        primary_image = first_variant.images.filter(is_primary=True).first()
        if not primary_image:
            primary_image = first_variant.images.first()
            
        # Add product data
        product_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else '',
            'brand': product.brand.name if product.brand else '',
            'price': float(first_variant.price) if first_variant.price else 0,
            'discount_price': float(first_variant.discount_price) if first_variant.discount_price else float(first_variant.price) if first_variant.price else 0,
            'image_url': primary_image.image.url if primary_image and hasattr(primary_image, 'image') else '/static/images/placeholder.svg',
            'total_stock': sum(size.stock for size in first_variant.sizes.all()) if first_variant.sizes.exists() else 0,
            'discount_percentage': int(((first_variant.price - first_variant.discount_price) / first_variant.price) * 100) if first_variant.discount_price and first_variant.price and first_variant.discount_price < first_variant.price else 0
        })

    return JsonResponse({
        'products': product_data
    })

def get_variant_data(request, variant_id, product_id=None):
    query_filters = {
        'id': variant_id,
        'is_active': True
    }
    if product_id:
        query_filters['product_id'] = product_id
    
    variant = get_object_or_404(
        Variant.objects.select_related('product')
        .prefetch_related('images', 'sizes'),
        **query_filters
    )
    
    # Get primary image, with fallback
    primary_image = variant.images.filter(is_primary=True).first()
    if not primary_image:
        primary_image = variant.images.first()
    
    data = {
        'success': True,
        'id': variant.id,
        'color': variant.color,
        'price': str(variant.price),
        'discount_price': str(variant.discount_price) if variant.discount_price else None,
        'images': [
            {
                'image': image.image.url,
                'is_primary': image.is_primary,
                'alt_text': f"{variant.color} {variant.product.name} view"
            } for image in variant.images.all()
        ],
        'sizes': [
            {
                'id': size.id,
                'name': size.name,
                'stock': size.stock
            } for size in variant.sizes.all()
        ],
        'primary_image_url': primary_image.image.url if primary_image else None
    }
    
    return JsonResponse(data)



def product_list(request):
    # Cache categories and brands since they don't change often
    categories = Category.objects.filter(is_active=True).only('id', 'name')
    brands = Brand.objects.filter(is_active=True).only('id', 'name')
    
    # Optimize initial product query
    base_variant_query = Variant.objects.filter(
        is_active=True
    ).select_related(
        'product'
    ).prefetch_related(
        'images',
        'sizes'
    ).annotate(
        stock_total=Sum('sizes__stock')
    )

    # Get initial products with optimized querying
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True,
        variants__is_active=True
    ).select_related(
        'category', 
        'brand'
    ).prefetch_related(
        Prefetch('variants', queryset=base_variant_query)
    ).distinct()
    
    # Apply filters if provided
    categories_filter = request.GET.get('categories')
    brands_filter = request.GET.get('brands')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_option = request.GET.get('sort', 'newest')  # Default sort is newest
    search_query = request.GET.get('search', '').strip()
    
    # Apply search filter if provided
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(brand__name__icontains=search_query)
        )
    
    # Apply category filter
    if categories_filter:
        category_ids = [cid for cid in categories_filter.split(',') if cid.isdigit()]
        if category_ids:
            products = products.filter(category_id__in=category_ids)
    
    # Apply brand filter
    if brands_filter:
        brand_ids = [bid for bid in brands_filter.split(',') if bid.isdigit()]
        if brand_ids:
            products = products.filter(brand_id__in=brand_ids)
    
    # Apply price filter
    if min_price or max_price:
        try:
            if min_price:
                min_price = float(min_price)
                products = products.filter(variants__price__gte=min_price)
            if max_price:
                max_price = float(max_price)
                products = products.filter(variants__price__lte=max_price)
            products = products.distinct()
        except (ValueError, TypeError):
            pass  # Invalid price format, ignore filter
    
    # Apply sorting
    if sort_option == 'price_low_high':
        products = products.annotate(
            min_price=Min('variants__price')
        ).order_by('min_price')
    elif sort_option == 'price_high_low':
        products = products.annotate(
            min_price=Min('variants__price')
        ).order_by('-min_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    elif sort_option == 'newest':
        products = products.order_by('-id')  # Using id as a proxy for newest items
    elif sort_option == 'popularity':
        products = products.annotate(
            total_sales=Count('variants__orderitem')
        ).order_by('-total_sales')

    # Paginate the products
    page = request.GET.get('page', 1)
    products_per_page = 12  # You can adjust this number
    paginator = Paginator(products, products_per_page)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    # Prepare product data for template
    product_data = []
    for product in products_page:
        variant_data = []
        total_stock = 0
        
        # Process variants
        for variant in product.variants.all():  # This is already filtered for active variants
            # Get primary image or first image
            primary_image = next(
                (img for img in variant.images.all() if img.is_primary),
                next((img for img in variant.images.all()), None)
            )
            
            # Calculate variant stock
            variant_stock = sum(size.stock for size in variant.sizes.all())
            total_stock += variant_stock
            
            # Determine final price (accounts for product/category offers via Variant.final_price)
            try:
                final_price_val = float(variant.final_price)
            except Exception:
                final_price_val = float(variant.price)

            # Calculate discount percentage based on final price
            discount_percentage = 0
            try:
                if variant.price and final_price_val < float(variant.price) and float(variant.price) > 0:
                    discount_percentage = int(((float(variant.price) - final_price_val) / float(variant.price)) * 100)
            except Exception:
                discount_percentage = 0
            
            # Default to None for image_url if no image exists
            image_url = None
            if primary_image and hasattr(primary_image, 'image'):
                try:
                    image_url = primary_image.image.url
                except:
                    image_url = None

            variant_data.append({
                'id': variant.id,
                'color': variant.color,
                'price': float(variant.price),
                'discount_price': float(variant.discount_price) if variant.discount_price else None,
                'final_price': final_price_val,
                'stock': variant_stock,
                'discount_percentage': discount_percentage,
                'image_url': image_url,  # This will be None if no image exists
                'sizes': [{'id': size.id, 'name': size.name, 'stock': size.stock} 
                         for size in variant.sizes.all()]
            })
        
        if not variant_data:  # Skip products with no valid variants
            continue
            
        # Use the first variant as the primary variant for display
        primary_variant = variant_data[0]
        
        product_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else 'Uncategorized',
            'brand': product.brand.name if product.brand else 'No Brand',
            'description': product.description,
            'primary_variant': primary_variant,
            'first_variant_id': variant_data[0]['id'] if variant_data else None,
            'total_stock': total_stock,
            'variants': variant_data,
            'rating': product.average_rating if hasattr(product, 'average_rating') else None,
            'review_count': product.review_count if hasattr(product, 'review_count') else 0,
        })
        
       
    # Pagination
    paginator = Paginator(product_data, 8)  # 12 products per page
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.get_page(page)
    except (PageNotAnInteger, EmptyPage):
        products_page = paginator.get_page(1)
    
    # Build pagination info for template
    pagination = {
        'current_page': products_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': products_page.has_previous(),
        'has_next': products_page.has_next(),
        'page_range': list(paginator.page_range),
        'total_items': paginator.count
    }

    # Active filters to preserve UI state
    active_filters = {
        'categories': categories_filter or '',
        'brands': brands_filter or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
        'sort': sort_option or 'newest',
        'search': search_query or ''
    }

    # Wishlist product ids and variant ids for UI (if user has wishlist)
    wishlist_product_ids = []
    wishlist_variant_ids = []
    try:
        if request.user.is_authenticated:
            wishlist = Wishlist.objects.filter(user=request.user).first()
            if wishlist:
                wishlist_product_ids = list(wishlist.variants.values_list('product__id', flat=True))
                wishlist_variant_ids = list(wishlist.variants.values_list('id', flat=True))
    except Exception:
        wishlist_product_ids = []
        wishlist_variant_ids = []

    context = {
        'products': products_page,
        'categories': categories,
        'brands': brands,
        'pagination': pagination,
        'active_filters': active_filters,
        'wishlist_product_ids': wishlist_product_ids,
        'wishlist_variant_ids': wishlist_variant_ids,
    }
    
    return render(request, 'product_list.html', context)

def product_detail(request, product_id):
    # Optimize variant query
    variant_query = Variant.objects.filter(
        is_active=True
    ).prefetch_related(
        'sizes',
        'images'
    ).annotate(
        stock_total=Sum('sizes__stock')
    )

    # Optimize product query with necessary related data
    product = get_object_or_404(
        Product.objects.select_related(
            'category', 
            'brand'
        ).prefetch_related(
            Prefetch('variants', queryset=variant_query),
            'reviews'  # If you have reviews
        ).annotate(
            total_stock=Sum('variants__sizes__stock'),
            avg_rating=Avg('reviews__rating')
        ),
        id=product_id,
        is_active=True
    )
    
    variants = product.variants.all()
    primary_variant = variants.first() if variants.exists() else None
    
    # Get all active variants with their images
    variants_with_images = []
    for variant in variants:
        # First try to get the primary image
        primary_image = variant.images.filter(is_primary=True).first()
        # If no primary image exists, fall back to the first image
        if not primary_image:
            primary_image = variant.images.first()
            
        variants_with_images.append({
            'variant': variant,
            'primary_image': primary_image,
            'id': variant.id,
            'color': variant.color,
        })
    
    # Size and stock handling for primary variant
    sizes = []
    default_size = None
    default_size_id = None
    if primary_variant:
        sizes = list(primary_variant.sizes.all().values('id', 'name', 'stock'))
        # Find first size with stock > 0 to set as default
        for size in sizes:
            if size['stock'] > 0:
                default_size = size['name']
                default_size_id = size['id']
                break
    
    # Calculate total stock for the primary variant
    total_stock = sum(size['stock'] for size in sizes) if sizes else 0
    
    # Get wishlist variant IDs for the current user
    wishlist_variant_ids = []
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.filter(
                user=request.user,
                is_active=True
            ).prefetch_related('variants').first()
            
            if wishlist:
                wishlist_variant_ids = list(wishlist.variants.values_list('id', flat=True))
        except Wishlist.DoesNotExist:
            wishlist_variant_ids = []
    
    context = {
        'product': product,
        'brand': product.brand.name,
        'primary_variant': primary_variant,
        'variants_with_images': variants_with_images,
        'sizes': sizes,
        'default_size': default_size,
        'default_size_id': default_size_id,
        'total_stock': total_stock,
        'selected_variant_id': primary_variant.id if primary_variant else None,
        'wishlist_variant_ids': wishlist_variant_ids,
    }
    
    return render(request, 'product_details.html', context)
######### CART ########




def view_cart(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login to access Cart")
        return redirect('Login')  # Redirect to login page if user is not authenticated
 
    # Clean up any duplicate carts first
    cleanup_carts(request.user)

    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(
        user=request.user,
        is_ordered=False,
        defaults={'is_active': True}
    )

    # Get all cart items
    cart_items = []
    for item in cart.items.select_related('variant', 'size').all():
        if item.is_active:
            if item.quantity > item.size.stock:
                new_quantity = item.size.stock
                if new_quantity <= 0:
                    item.delete()
                    continue
                else:
                    item.quantity = new_quantity
                    item.save()
            # Only add to cart if quantity > 0 after adjustment
            if item.quantity > 0:
                cart_items.append(item)
            else:
                item.delete()
        else:
            continue

    # Get wishlist variant IDs for UI
    wishlist_variant_ids = []
    try:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_variant_ids = list(wishlist.variants.values_list('id', flat=True))
    except Exception:
        pass
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.total_price,
        'total_discount': cart.total_discount,
        'final_price': cart.final_price,
        'wishlist_variant_ids': wishlist_variant_ids
    }

    return render(request, 'cart.html', context)



logger = logging.getLogger(__name__)
def cleanup_carts(user):
    """
    Ensures a user has only ONE active, unordered cart.
    Deletes older duplicate carts to prevent conflicts.
    """
    # Get all unordered carts for the user, ordered newest first
    carts = Cart.objects.filter(
        user=user, 
        is_ordered=False
    )

    # If multiple carts exist, keep only the newest one
    if carts.count() > 1:
        # Preserve the most recent cart
        latest_cart = carts.first()
        # Delete all older carts
        carts.exclude(id=latest_cart.id).delete()
        
@require_POST
@transaction.atomic
def add_to_cart(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Please log in to add items to your cart'}, status=403)

        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        size_name = request.POST.get('size_name')

        if not variant_id or quantity < 1 or not size_name:
            return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)

        try:
            variant = Variant.objects.get(id=variant_id)
        except Variant.DoesNotExist:
            return JsonResponse({'success': False, 'message': f'Variant with ID {variant_id} not found'}, status=404)
        
        try:
            size = Size.objects.get(name=size_name, product_variant=variant)
        except Size.DoesNotExist:
            # Debug: show available sizes
            available_sizes = Size.objects.filter(product_variant=variant).values_list('name', flat=True)
            return JsonResponse({
                'success': False, 
                'message': f'Size "{size_name}" not found for this variant. Available sizes: {list(available_sizes)}'
            }, status=404)

        # Check if the product, category, brand, and variant are active
        if not (variant.is_active and variant.product.is_active and variant.product.category.is_active and variant.product.brand.is_active):
            return JsonResponse({'success': False, 'message': 'This product is no longer available'}, status=400)

        # Check size stock
        if size.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {size.stock} items available in {size.get_name_display()} size'
            }, status=400)

        cleanup_carts(request.user)

        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            is_ordered=False,
            defaults={'is_active': True}
        )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            size=size,
            defaults={'quantity': 0}
        )

        # Check combined quantity against size stock
        if (cart_item.quantity + quantity) > size.stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {size.stock - cart_item.quantity} more available in {size.get_name_display()} size'
            }, status=400)

        cart_item.quantity += quantity
        cart_item.save()

        cart_count = sum(item.quantity for item in cart.items.all())

        return JsonResponse({
            'success': True,
            'message': 'Item added to cart successfully',
            'cart_count': cart_count,
        })

    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            cart_item.delete()
            return JsonResponse({'success': True, 'message': 'Item removed from cart successfully!'})
        except Exception as e:

            print(f"Payment verification failed with error: {str(e)}")

            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
@require_POST
def update_quantity(request, item_id):
    try:
        data = json.loads(request.body)
        quantity_change = int(data.get('quantity_change', 0))
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart = cart_item.cart
        
        # Calculate new quantity
        new_quantity = cart_item.quantity + quantity_change
        
        # Validate new quantity against size stock
        if new_quantity < 1:
            return JsonResponse({
                'success': False, 
                'message': 'Quantity cannot be less than 1.'
            })
            
        if new_quantity > cart_item.size.stock:
            return JsonResponse({
                'success': False, 
                'message': f'Only {cart_item.size.stock} items available in {cart_item.size.get_name_display()} size'
            })
        
        # Update quantity
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Calculate updated totals
        item_total = cart_item.variant.price * new_quantity
        
        return JsonResponse({
            'success': True,
            'message': 'Quantity updated successfully!',
            'new_quantity': new_quantity,
            'cart_total': float(cart.total_price),
            'cart_final': float(cart.final_price), 
            'item_total': float(item_total),
            'size_stock': cart_item.size.stock
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid request data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating quantity: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'message': str(e)
        }, status=500)
    


@login_required(login_url='Login')
def wishlist_view(request):
    try:
        # Get or create single wishlist for user
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Get all active variants in wishlist
        wishlist_items = wishlist.variants.filter(
            is_active=True,
            product__is_active=True
        ).select_related(
            'product'
        ).prefetch_related('images')

        items_data = []
        product_categories = set()  # To collect categories for similar products
        product_ids = set()  # To exclude wishlist products from similar products
        
        for variant in wishlist_items:
            try:
                # Get primary image or first image
                primary_image = variant.images.filter(is_primary=True).first()
                if not primary_image:
                    primary_image = variant.images.first()
                
                # Get image URL safely
                image_url = None
                if primary_image and hasattr(primary_image, 'image'):
                    image_url = primary_image.image.url
                
                # Calculate stock safely
                try:
                    stock = sum(size.stock for size in variant.sizes.all())
                except Exception:
                    stock = 0
                
                # Calculate final price considering offers
                original_price = float(variant.price or 0)
                final_price = float(variant.final_price)
                savings = original_price - final_price
                
                # Check if this variant is already in the cart
                is_in_cart = False
                try:
                    cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
                    if cart:
                        is_in_cart = CartItem.objects.filter(cart=cart, variant=variant).exists()
                except Exception:
                    pass
                
                items_data.append({
                    'id': variant.id,
                    'product_id': variant.product.id if variant.product else None,
                    'product_name': variant.product.name if variant.product else 'Unknown Product',
                    'color': variant.color or 'No Color',
                    'original_price': original_price,
                    'final_price': final_price,
                    'savings': savings,
                    'image_url': image_url,
                    'stock': stock,
                    'has_offer': variant.active_offer is not None,
                    'is_in_cart': is_in_cart
                })
            except Exception as item_error:
                print(f"Error processing wishlist item: {str(item_error)}")
            
            # Collect category and product ID for similar products
            if variant.product.category:
                product_categories.add(variant.product.category.id)
            product_ids.add(variant.product.id)
        
        # Get similar products based on categories
        similar_products = []
        if product_categories:
            # Get products from the same categories but not in the wishlist
            similar_products_query = Product.objects.filter(
                category__id__in=product_categories,
                is_active=True
            ).exclude(
                id__in=product_ids
            ).distinct().prefetch_related(
                'variants', 'variants__images'
            )[:8]  # Limit to 8 similar products
            
            # Prepare similar products data
            for product in similar_products_query:
                try:
                    # Get first active variant
                    first_variant = product.variants.filter(is_active=True).first()
                    if first_variant:
                        # Get primary image or first image
                        primary_image = first_variant.images.filter(is_primary=True).first()
                        if not primary_image:
                            primary_image = first_variant.images.first()
                        
                        # Get image URL safely
                        image_url = None
                        if primary_image and hasattr(primary_image, 'image'):
                            image_url = primary_image.image.url
                        
                        similar_products.append({
                            'id': product.id,
                            'name': product.name if product.name else 'Unknown Product',
                            'original_price': float(first_variant.price or 0),
                            'final_price': float(first_variant.final_price),
                            'savings': float(first_variant.price or 0) - float(first_variant.final_price),
                            'image_url': image_url
                        })
                except Exception as product_error:
                    print(f"Error processing similar product: {str(product_error)}")

        # Calculate total value and savings for wishlist summary
        wishlist_total = sum(item['final_price'] for item in items_data)
        wishlist_savings = sum(item['savings'] for item in items_data)

        return render(request, 'wishlist.html', {
            'wishlist_items': items_data,
            'similar_products': similar_products,
            'wishlist_total': wishlist_total,
            'wishlist_savings': wishlist_savings
        })
        
    except Exception as e:
        import traceback
        print(f"Wishlist error: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Error loading wishlist: {str(e)}")
        return redirect('home')

@login_required
def move_to_wishlist(request, variant_id):
    try:
        variant = Variant.objects.get(id=variant_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        if variant in wishlist.variants.all():
            wishlist.variants.remove(variant)
            message = 'Removed from wishlist'
        else:
            wishlist.variants.add(variant)
            message = 'Added to wishlist'
            
        return JsonResponse({
            'success': True,
            'message': message,
            'wishlist_count': wishlist.variants.count()
        })
    except Variant.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        })

# @login_required
# def get_wishlist_items(request):
#     """Fetch wishlist items for AJAX requests"""
#     wishlist_items = Wishlist.objects.filter(user=request.user).select_related('variant__product')
#     items = [{
#         'id': item.id,
#         'name': item.variant.product.name,
#         'description': item.variant.product.description[:100],  # Trim description
#         'price': float(item.variant.price),
#         'image': item.variant.images.first().image.url if item.variant.images.exists() else '/static/default-image.jpg',

#     } for item in wishlist_items]
#     return JsonResponse(items, safe=False)


@login_required
@require_POST
def remove_from_wishlist(request, variant_id):
    """Remove item from wishlist"""
    try:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        variant = Variant.objects.get(id=variant_id)
        
        if variant in wishlist.variants.all():
            wishlist.variants.remove(variant)
            return JsonResponse({
                'success': True, 
                'message': 'Item removed from wishlist',
                'wishlist_count': wishlist.variants.count()
            })
        else:
            return JsonResponse({'success': False, 'message': 'Item not found in wishlist'})
    except Variant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product variant not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error removing item from wishlist'})

# Optional: Add to wishlist directly from products
@login_required
@require_POST
def add_to_wishlist(request, variant_id):
    """Add item directly to wishlist"""
    try:
        variant = get_object_or_404(Variant, id=variant_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist.variants.add(variant)
        return JsonResponse({'success': True, 'message': 'Added to wishlist!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error adding to wishlist'})

@login_required
def sort_wishlist(request, sort_by):
    """Sort wishlist items"""
    try:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        items = wishlist.variants.filter(
            is_active=True,
            product__is_active=True
        ).select_related('product').prefetch_related('images')
        
        if sort_by == 'newest':
            items = items.order_by('-created_at')
        elif sort_by == 'price-low':
            items = items.order_by('discount_price', 'price')
        elif sort_by == 'price-high':
            items = items.order_by('-discount_price', '-price')
        elif sort_by == 'discount':
            items = items.annotate(
                discount_percent=ExpressionWrapper(
                    (F('price') - F('discount_price')) * 100.0 / F('price'),
                    output_field=FloatField()
                )
            ).order_by('-discount_percent')
        elif sort_by == 'name':
            items = items.order_by('product__name')
        
        # Get user's cart for checking if items are already in cart
        cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
        cart_variant_ids = set()
        if cart:
            cart_variant_ids = set(CartItem.objects.filter(cart=cart).values_list('variant_id', flat=True))
        
        items_data = [{
            'id': item.id,
            'product_id': item.product.id if item.product else None,
            'product_name': item.product.name if item.product else 'Product Unavailable',
            'color': item.color,
            'original_price': float(item.price or 0),
            'final_price': float(item.final_price),
            'savings': float(item.price or 0) - float(item.final_price),
            'image_url': item.images.filter(is_primary=True).first().image.url if item.images.filter(is_primary=True).exists() else item.images.first().image.url if item.images.exists() else None,
            'stock': sum(size.stock for size in item.sizes.all()),
            'has_offer': item.active_offer is not None,
            'is_in_cart': item.id in cart_variant_ids
        } for item in items]
        
        return JsonResponse({
            'success': True,
            'items': items_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def load_similar_products(request):
    """Load similar products based on wishlist items"""
    try:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist_items = wishlist.variants.filter(
            is_active=True,
            product__is_active=True
        ).select_related('product')
        
        # Collect categories and product IDs
        product_categories = set()
        product_ids = set()
        for item in wishlist_items:
            if item.product.category:
                product_categories.add(item.product.category.id)
            product_ids.add(item.product.id)
        
        # Get similar products
        similar_products = []
        if product_categories:
            products = Product.objects.filter(
                category__id__in=product_categories,
                is_active=True
            ).exclude(
                id__in=product_ids
            ).distinct().prefetch_related(
                'variants',
                'variants__images'
            )[:8]
            
            for product in products:
                variant = product.variants.filter(is_active=True).first()
                if variant:
                    image = variant.images.filter(is_primary=True).first() or variant.images.first()
                    similar_products.append({
                        'id': product.id,
                        'name': product.name,
                        'price': variant.price,
                        'discount_price': variant.discount_price,
                        'image_url': image.image.url if image else None
                    })
        
        return JsonResponse({
            'success': True,
            'products': similar_products
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
@require_POST
def clear_wishlist(request):
    """Clear all items from wishlist"""
    try:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist.variants.clear()
        return JsonResponse({'success': True, 'message': 'Wishlist cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing wishlist: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'Error clearing wishlist'})

@login_required
@require_POST
def add_multiple_to_cart(request):
    """Add multiple wishlist items to cart"""
    try:
        # Get user's wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Get all active variants in the wishlist
        wishlist_variants = wishlist.variants.filter(
            is_active=True, 
            product__is_active=True
        ).prefetch_related('sizes')
        
        if not wishlist_variants.exists():
            return JsonResponse({'success': False, 'message': 'No items in wishlist'})
        
        # Get or create user's cart
        cart = Cart.objects.get_or_create(
            user=request.user, 
            is_ordered=False, 
            defaults={'is_active': True}
        )[0]
        
        added_count = 0
        skipped_count = 0
        error_messages = []
        
        # Process each variant in the wishlist
        for variant in wishlist_variants:
            try:
                # Check if this variant is already in cart (any size)
                if CartItem.objects.filter(cart=cart, variant=variant).exists():
                    skipped_count += 1
                    error_messages.append(f"{variant.product.name} ({variant.color}): Already in cart")
                    continue
                
                # Get available sizes with stock
                available_sizes = variant.sizes.filter(stock__gt=0).order_by('name')
                
                if not available_sizes.exists():
                    skipped_count += 1
                    error_messages.append(f"{variant.product.name} ({variant.color}): No sizes in stock")
                    continue
                
                # Get the first available size
                size = available_sizes.first()
                
                # Add to cart (we already checked it's not there)
                CartItem.objects.create(
                    cart=cart,
                    variant=variant,
                    size=size,
                    quantity=1
                )
                
                added_count += 1
                
            except Exception as item_error:
                skipped_count += 1
                error_messages.append(f"Error adding {variant.product.name if hasattr(variant, 'product') else 'item'}")
                logger.error(f"Error adding item to cart: {str(item_error)}", exc_info=True)
        
        # Calculate total cart count
        cart_count = CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Check if all items were already in cart
        already_in_cart_count = sum(1 for msg in error_messages if 'Already in cart' in msg)
        
        # Prepare response
        if added_count > 0:
            message = f'{added_count} item(s) added to cart'
            if skipped_count > 0:
                message += f', {skipped_count} item(s) skipped'
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'cart_count': cart_count,
                'added_count': added_count,
                'skipped_count': skipped_count,
                'errors': error_messages[:5]  # Limit to first 5 errors
            })
        else:
            # Check if all items were already in cart
            if already_in_cart_count == wishlist_variants.count():
                message = 'All wishlist items are already in your cart'
            elif skipped_count > 0:
                message = 'No new items could be added. Items may be out of stock or already in cart'
            else:
                message = 'No items available to add'
                
            return JsonResponse({
                'success': True,  # Changed to True to avoid showing error toast
                'message': message,
                'cart_count': cart_count,
                'added_count': 0,
                'skipped_count': skipped_count,
                'info': error_messages[:5]  # Show as info instead of errors
            })
            
    except Exception as e:
        logger.error(f"Error in add_multiple_to_cart: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'Error adding items to cart: {str(e)}'})

@login_required(login_url='Login')
def user_profile(request, user_id):
    # Ensure user can only access their own profile
    if request.user.id != user_id:
        messages.error(request, "You are not authorized to view this profile.")
        return redirect('user_profile', user_id=request.user.id)
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Handle profile update
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Validation
        errors = []
        if not full_name:
            errors.append("Full name cannot be empty.")
        
        if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
            errors.append("Invalid phone number format.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'profile.html', {
                'user': user,
                'full_name': full_name,
                'phone': phone,
                'email': user.email,
                'referral_code': user.referral_code or 'N/A',
            })
        
        # Update user profile
        # Split full_name into first_name and last_name
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.full_name = full_name
        user.phone = phone
        user.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('user_profile', user_id=user.id)
    
    # GET request
    # Combine first_name and last_name if full_name is not set
    display_full_name = user.full_name
    if not display_full_name:
        display_full_name = f"{user.first_name} {user.last_name}".strip() if user.first_name or user.last_name else ""
    
    context = {
        'user': user,
        'full_name': display_full_name,
        'email': user.email,
        'phone': user.phone or '',
        'referral_code': user.referral_code or 'N/A',
    }
    return render(request, 'profile.html', context)




################## Addresss ####################


@never_cache
@login_required(login_url='Login')
def userManageAddress(request):
    user_addresses = Address.objects.filter(user=request.user, is_deleted=False)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            try:
                address = form.save(commit=False)
                address.user = request.user
                
                # Handle default address setting
                if address.is_default:
                    with transaction.atomic():
                        Address.objects.filter(user=request.user).update(is_default=False)
                
                address.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Address added successfully'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e),
                    'form_data': request.POST.dict()
                })
        else:
            # Get first error message for each field
            error_messages = []
            for field, errors in form.errors.items():
                field_name = field.replace('_', ' ').title()
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            return JsonResponse({
                'success': False,
                'message': error_messages[0] if error_messages else 'Invalid form data',
                'errors': form.errors,
                'form_data': request.POST.dict()
            })

    context = {
        'addresses': user_addresses,
    }
    return render(request, 'usermanageaddress.html', context)

@login_required(login_url='Login')
@never_cache
def editAddress(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user, is_deleted=False)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            
            # Handle default address setting
            if address.is_default:
                with transaction.atomic():
                    Address.objects.filter(user=request.user).exclude(id=address_id).update(is_default=False)
            
            address.save()
            return redirect('userManageAddress')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'usereditaddress.html', {'form': form, 'address': address})

@login_required(login_url='Login')
@never_cache
def deleteAddress(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_deleted = True
    address.save()
    return JsonResponse({'success': True, 'message': 'Address deleted successfully'})

@login_required(login_url='Login')
@csrf_exempt
def set_primary_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            address_id = data.get('address_id')
            
            with transaction.atomic():
                # First, unset all default addresses
                Address.objects.filter(user=request.user).update(is_default=False)
                # Then set the selected address as default
                address = Address.objects.get(id=address_id, user=request.user)
                address.is_default = True
                address.save()
            
            return JsonResponse({'success': True})
        except Address.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Address not found'}, status=404)
        except Exception as e:

            print(f"Payment verification failed with error: {str(e)}")

            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)



################ checout #####################



## this for validate the cart 
@login_required
def validate_cart(request):
    cart = Cart.objects.filter(
        user=request.user,
        is_ordered=False
    ).prefetch_related('items').first()

    is_valid = True
    errors = []

    if cart:
        for item in cart.items.all():
            if not item.is_active:
                is_valid = False
                errors.append(f"{item.variant.product.name} is unavailable")
                item.delete()

    return JsonResponse({
        'is_valid': is_valid,
        'errors': errors
    })


# Configure logging
logger = logging.getLogger(__name__)
@login_required(login_url='Login')
@never_cache
def user_checkout(request):
    try:
        with transaction.atomic():
            # Get cart and related items
            cart = Cart.objects.filter(
                user=request.user, 
                is_ordered=False
            ).prefetch_related(
                'items__variant__product',
                'items__size'
            ).first()
            
            if not cart or not cart.items.exists():
                messages.warning(request, "Your cart is empty")
                return redirect('view_cart')
            
            # Update and validate cart totals
            cart.update_totals()
            
            # Validate cart items
            cart_items = []
            total_quantity = 0
            for item in cart.items.all():
                if not item.is_active:
                    messages.warning(request, f"{item.variant.product.name} is no longer available")
                    item.delete()
                    continue
                
                if item.quantity > item.size.stock:
                    messages.warning(request, f"Only {item.size.stock} units available for {item.variant.product.name}")
                    item.quantity = item.size.stock
                    item.save()
                    if item.quantity == 0:
                        item.delete()
                        continue
                
                cart_items.append(item)
                total_quantity += item.quantity
            
            if not cart_items:
                messages.warning(request, "No valid items in cart")
                return redirect('view_cart')
            
            # Get addresses and payment methods
            user_addresses = Address.objects.filter(user=request.user, is_deleted=False)
            payment_methods = PAYMENT_METHODS
            
            # Calculate totals using Decimal
            subtotal = cart.total_price
            # Calculate product discount (includes ProductOffer, CategoryOffer, and manual discount_price)
            product_discount = Decimal(str(sum(
                (item.variant.price - item.variant.final_price) * item.quantity
                for item in cart_items
                if item.variant.final_price < item.variant.price
            )))
            coupon_discount = cart.calculate_coupon_discount()
            total_discount = product_discount + coupon_discount
            final_price = cart.final_price
            delivery_charge = Decimal('0.00')  # Free delivery
            final_amount = final_price
            
            # Get available coupons
            today = timezone.now().date()
            coupons = Coupon.objects.filter(
                is_active=True,
                start_date__lte=today,
                end_date__gte=today
            )
            
            coupon_data = []
            for coupon in coupons:
                coupon_min_purchase = Decimal(str(coupon.minimum_purchase))
                
                # Check how many times the user has used this coupon
                user_usage_count = CouponUsage.objects.filter(user=request.user, coupon=coupon).count()
                
                # Check if user can still use this coupon
                can_use = user_usage_count < coupon.usage_limit
                
                # Check minimum purchase requirement
                meets_minimum = subtotal >= coupon_min_purchase
                
                # Coupon is applicable if both conditions are met
                is_applicable = can_use and meets_minimum
                
                amount_needed = coupon_min_purchase - subtotal if subtotal < coupon_min_purchase else Decimal('0')
                
                coupon_data.append({
                    'code': coupon.code,
                    'type': coupon.type,
                    'value': float(coupon.value),
                    'minimum_purchase': float(coupon.minimum_purchase),
                    'is_applicable': is_applicable,
                    'expiry_date': coupon.end_date,
                    'amount_needed': float(amount_needed),
                    'usage_count': user_usage_count,
                    'usage_limit': coupon.usage_limit,
                    'can_use': can_use
                })
            
            context = {
                'user_addresses': user_addresses,
                'cart_items': cart_items,
                'payment_methods': payment_methods,
                'total_quantity': total_quantity,
                'subtotal': float(subtotal),
                'product_discount': float(product_discount),
                'coupon_discount': float(coupon_discount),
                'total_discount': float(total_discount),
                'final_price': float(final_price),
                'delivery_charge': float(delivery_charge),
                'final_amount': float(final_amount),
                'cart': cart,
                'coupons': coupon_data
            }
            
            return render(request, 'checkout.html', context)
    
    except Exception as e:
        logger.error(f"Checkout error for user {request.user.id}: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('view_cart')
    

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(['POST'])
def place_order(request):
    if request.method == 'POST':
        try:
            address_id = request.POST.get('address_id')
            payment_method = request.POST.get('payment_method')
            
            if not address_id:
                return JsonResponse({'success': False, 'message': 'Please select a delivery address'})

            # Get the address
            try:
                address = Address.objects.get(id=address_id, user=request.user)
            except Address.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid address'})

            # Get the cart
            cart = Cart.objects.get(user=request.user, is_ordered=False)
            if not cart.items.exists():
                return JsonResponse({'success': False, 'message': 'Your cart is empty'})

            # Get or create payment methods if they don't exist
            cod_method, _ = PaymentMethod.objects.get_or_create(
                name='COD'
            )
            razorpay_method, _ = PaymentMethod.objects.get_or_create(
                name='Razorpay'
            )

            # Set payment method based on selection
            if payment_method == 'razorpay':
                payment_method_id = razorpay_method.id
            else:
                payment_method_id = cod_method.id

            # Calculate discounts
            cart_items = cart.items.all()
            product_discount = Decimal(str(sum(
                (item.variant.price - item.variant.final_price) * item.quantity
                for item in cart_items
                if item.variant.final_price < item.variant.price
            )))
            coupon_discount = cart.calculate_coupon_discount()

            # Create the order
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.final_price,
                product_discount=product_discount,
                coupon_discount=coupon_discount,
                paymentmethod_id=payment_method_id,
                full_name=address.full_name,
                email=address.email,
                phone=address.phone,
                address_line1=address.address_line1,
                address_line2=address.address_line2,
                city=address.city,
                state=address.state,
                pincode=address.pincode
            )

            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.variant.product,
                    variant=cart_item.variant,
                    size=cart_item.size,
                    quantity=cart_item.quantity,
                    price=cart_item.variant.discount_price or cart_item.variant.price,  # Price paid
                    original_price=cart_item.variant.price  # MRP
                )

            # If Razorpay payment
            if payment_method == 'razorpay':
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                amount_in_paise = int(order.total_amount * 100)
                razorpay_order = client.order.create({
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "payment_capture": "1"
                })
                order.razorpay_order_id = razorpay_order['id']
                order.save()
                
                return JsonResponse({
                    'success': True,
                    'razorpay_order_id': razorpay_order['id'],
                    'amount': amount_in_paise,
                })
            else:
                # For COD
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('order_confirmation', args=[order.id])
                })

        except Exception as e:
            logger.error(f"Error in place_order: {str(e)}")
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def download_invoice(request, order_id):
    try:
        # Get the order and verify ownership
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Generate the invoice PDF. generate_invoice_pdf historically
        # returned a filename (string) pointing to a file under MEDIA_ROOT/invoices/.
        # A newer implementation may return an HttpResponse directly.
        result = generate_invoice_pdf(order)

        # If the generator already returned an HttpResponse (in-memory PDF), return it directly
        if isinstance(result, HttpResponse):
            return result

        # Otherwise assume we received a filename and read the file from disk
        filename = result
        file_path = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

        raise Http404()
        
    except Exception as e:
        raise Http404(str(e))

def payment_success(request, order_id=None):
    if request.method == "POST":
        try:
            # Log the incoming request for debugging
            logger.info(f"Payment success request received with order_id={order_id}")
            
            data = json.loads(request.body)
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')
            
            logger.info(f"Payment data: razorpay_order_id={razorpay_order_id}, razorpay_payment_id={razorpay_payment_id}")

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # First, try to find the order by razorpay_order_id
            order = None
            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                logger.info(f"Found order by razorpay_order_id: {order.order_id} (ID: {order.id})")
            except Order.DoesNotExist:
                logger.warning(f"Order not found by razorpay_order_id: {razorpay_order_id}")
                
                # If not found, try by the provided order_id parameter
                if order_id:
                    logger.info(f"Trying to find order by order_id parameter: {order_id}")
                    
                    # First, try exact match on order_id field
                    try:
                        order = Order.objects.get(order_id=order_id)
                        logger.info(f"Found order by exact order_id match: {order.order_id} (ID: {order.id})")
                    except Order.DoesNotExist:
                        # Try to find by numeric ID or partial match
                        try:
                            # Try numeric ID first
                            order = Order.objects.get(id=int(order_id))
                            logger.info(f"Found order by numeric ID: {order.order_id} (ID: {order.id})")
                        except (ValueError, Order.DoesNotExist):
                            # Try partial match on order_id
                            order = Order.objects.filter(order_id__icontains=str(order_id)).first()
                            if order:
                                logger.info(f"Found order by partial order_id match: {order.order_id} (ID: {order.id})")
                            else:
                                logger.error(f"Order not found by any method with order_id: {order_id}")
                                raise Order.DoesNotExist("Order not found")

            try:
                # Verify payment signature
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })
                
                # Update order status for successful payment
                order.payment_status = 'PAID'
                order.order_status = 'PENDING'
                order.razorpay_payment_id = razorpay_payment_id
                # Reduce stock for each order item
                for item in order.order_items.all():
                    size = item.size
                    if size:
                        if size.stock >= item.quantity:
                            size.stock -= item.quantity
                            size.save()
                        else:
                            logger.error(f"Insufficient stock for {item.variant.product.name} in size {size.name} during payment success. Only {size.stock} available.")
                            # Optionally, handle this edge case (should not happen if checked at order time)
                # Mark the user's cart as ordered and create a new cart
                try:
                    user_carts = Cart.objects.filter(user=order.user, is_ordered=False)
                    if user_carts.exists():
                        cart = user_carts.first()
                        cart.is_ordered = True
                        cart.save()
                        new_cart = Cart.objects.create(user=order.user)
                        logger.info(f"Marked cart as ordered and created new cart for user {order.user.id}")
                    # Remove this order from pending orders in session if it exists
                    if 'pending_orders' in request.session and order.order_id in request.session['pending_orders']:
                        pending_orders = request.session['pending_orders']
                        pending_orders.remove(order.order_id)
                        request.session['pending_orders'] = pending_orders
                        request.session.modified = True
                        logger.info(f"Removed order {order.order_id} from pending orders in session")
                except Exception as cart_error:
                    logger.error(f"Error handling cart after successful payment: {str(cart_error)}")
                order.save()
                
                # Verify the order exists in the database again before redirecting
                try:
                    # Double-check that the order exists and can be accessed
                    check_order = Order.objects.get(order_id=order.order_id)
                    logger.info(f"Verified order exists with order_id={order.order_id}")
                    
                    # Get the URL for the order details page
                    redirect_url = reverse('order_details', args=[order.order_id])
                    logger.info(f"Generated redirect URL: {redirect_url}")
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Payment successful',
                        'redirect_url': redirect_url
                    })
                except Order.DoesNotExist:
                    logger.error(f"Critical error: Order {order.order_id} exists during payment but not during redirect")
                    # Fallback to my-orders page
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Payment successful, but order details not found',
                        'redirect_url': reverse('my_orders')
                    })

            except Exception as e:
                # Payment verification failed - update order status
                order.payment_status = 'FAILED'
                order.payment_failure_reason = str(e)
                order.payment_attempts += 1
                order.last_payment_attempt = timezone.now()
                
                # Set or update payment expiry time (10 minutes from now)
                order.payment_expiry_time = timezone.now() + timezone.timedelta(minutes=10)
                order.save()
                
                # Return JSON with error status and payment retry information
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment verification failed. You can retry payment from the orders page.',
                    'redirect_url': reverse('my_orders'),
                    'payment_retry': {
                        'can_retry': True,
                        'expiry_time': order.payment_expiry_time.isoformat(),
                        'order_id': order.order_id
                    }
                })

        except Order.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Order not found',
                'redirect_url': reverse('my_orders')
            }, status=404)
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while processing payment',
                'redirect_url': reverse('my_orders')
            }, status=400)

    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request',
        'redirect_url': reverse('my_orders')
    }, status=400)

@login_required
@login_required
def retry_payment(request, order_id):
    try:
        # Add debugging logs
        logger.info(f"Retry payment request for order_id: {order_id} by user: {request.user.id}")
        
        order = Order.objects.get(order_id=order_id, user=request.user)
        logger.info(f"Found order: {order.order_id} with current razorpay_order_id: {order.razorpay_order_id}")
        
        # Check if order is already paid
        if order.payment_status == 'PAID':
            logger.warning(f"Order {order_id} is already paid")
            return JsonResponse({
                'status': 'error',
                'message': 'Order is already paid'
            })
        
        # Check if payment has expired
        now = timezone.now()
        if order.payment_expiry_time and now > order.payment_expiry_time:
            # Auto-cancel the order if payment time has expired
            order.order_status = 'CANCELLED'
            order.payment_status = 'FAILED'
            order.cancelled_at = now
            order.payment_failure_reason = 'Payment time expired'
            order.save()
            
            # Create status history entry
            OrderStatusHistory.objects.create(
                order=order,
                old_status='PENDING',
                new_status='CANCELLED',
                reason='Payment time expired'
            )
            
            return JsonResponse({
                'status': 'error',
                'message': 'Payment time has expired. Order has been cancelled.',
                'redirect_url': reverse('my_orders')
            })

        # Create new Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment = client.order.create({
            'amount': int(order.total_amount * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1
        })
        
        logger.info(f"Created new Razorpay order: {payment['id']} for order: {order.order_id}")
        logger.info(f"Razorpay response: {payment}")
        
        # Update order with new Razorpay order ID and reset payment expiry time
        old_razorpay_id = order.razorpay_order_id
        order.razorpay_order_id = payment['id']
        order.payment_status = 'PAYMENT_PENDING'
        order.payment_attempts += 1
        order.last_payment_attempt = now
        order.payment_expiry_time = now + timezone.timedelta(minutes=10)  # Reset to 10 minutes from now
        order.save()
        
        logger.info(f"Updated order {order.order_id}: old_razorpay_id={old_razorpay_id}, new_razorpay_id={order.razorpay_order_id}")
        
        # Get customer details for prefill
        customer_name = order.full_name or request.user.get_full_name() or request.user.username
        customer_email = order.email or request.user.email
        customer_phone = order.phone or ''
        
        return JsonResponse({
            'status': 'success',
            'order_id': payment['id'],
            'amount': int(order.total_amount * 100),
            'key': settings.RAZORPAY_KEY_ID,
            'expiry_time': order.payment_expiry_time.isoformat(),
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone
        })
        
    except Order.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
def retry_payment_form(request, order_id):
    """Form-based retry payment - creates Razorpay order and renders checkout page"""
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        
        # Check if order is already paid
        if order.payment_status == 'PAID':
            messages.error(request, 'Order is already paid')
            return redirect('my_orders')
        
        # Check if payment has expired - CANCEL THE ORDER
        now = timezone.now()
        if order.payment_expiry_time and now > order.payment_expiry_time:
            # Auto-cancel expired order
            order.order_status = 'CANCELLED'
            order.payment_status = 'FAILED'
            order.cancelled_at = now
            order.payment_failure_reason = 'Payment time expired - Order cancelled'
            order.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                old_status='PENDING',
                new_status='CANCELLED',
                reason='Payment deadline expired'
            )
            
            messages.error(request, 'Payment time has expired. Your order has been cancelled.')
            return redirect('my_orders')
        
        # Create new Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment = client.order.create({
            'amount': int(order.total_amount * 100),
            'currency': 'INR',
            'payment_capture': 1
        })
        
        # Update order with new Razorpay order ID
        order.razorpay_order_id = payment['id']
        order.payment_status = 'PAYMENT_PENDING'
        order.payment_attempts += 1
        order.last_payment_attempt = now
        order.payment_expiry_time = now + timezone.timedelta(minutes=10)
        order.save()
        
        # Render checkout with Razorpay details
        context = {
            'order': order,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': payment['id'],
            'amount': int(order.total_amount * 100),
            'customer_name': order.full_name or request.user.get_full_name() or request.user.username,
            'customer_email': order.email or request.user.email,
            'customer_phone': order.phone or ''
        }
        return render(request, 'retry_payment.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('my_orders')
    except Exception as e:
        logger.error(f"Error in retry_payment_form: {str(e)}")
        messages.error(request, 'An error occurred while processing your request')
        return redirect('my_orders')



################# Order ####################
from manager.models import Order, OrderItem, Cart, CartItem, Coupon, CouponUsage
# @login_required
# def order_confirmation(request, order_number):
#     try:
#         order = Order.objects.select_related('user', 'payment_method').prefetch_related(
#             'order_items',
#             'order_items__variant',
#             'order_items__variant__product'
#         ).get(order_number=order_number, user=request.user)
        
#         return render(request, 'order_confirmation.html', {'order': order})
#     except Order.DoesNotExist:
#         messages.error(request, 'Order not found')
#         return redirect('my_orders')

def my_orders(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login to access Cart")
        return redirect('Login')  # Redirect to login page if user is not authenticated
    
    orders = Order.objects.filter(user=request.user)\
        .prefetch_related(
            'order_items',
            'order_items__product',
            'order_items__variant',
            'order_items__variant__images',
                'order_items__size'  # Add size to prefetch
        )\
        .select_related('payment_method')\
        .order_by('-created_at')
        
    logger.debug(f"Fetched {orders.count()} orders for user {request.user.id}")
    
    for order in orders:
        logger.debug(f"Order {order.id} status: {order.order_status}")
    
    context = {'orders': orders}
    return render(request, 'my_orders.html', context)

@login_required(login_url='Login')
def order_details(request, order_id):
    try:
        order = get_object_or_404(
            Order.objects.prefetch_related(
                'order_items',
                'order_items__product',
                'order_items__variant',
                'order_items__variant__images',
                'order_items__size',
                'admin_responses'
            ),
            order_id=order_id,
            user=request.user
        )
        order_items = order.order_items.all()
        logger.debug(f"Fetched order details for order {order_id}")
        
        # Prepare timeline events
        timeline = []
        
        # Order Placed (Always shown)
        timeline.append({
            'status': 'Order Placed',
            'date': order.created_at,
            'description': f'Order #{order.order_id} has been placed successfully'
        })
        
        # Add admin responses to timeline
        for response in order.admin_responses.all():
            timeline.append({
                'status': 'Admin Response',
                'date': response.created_at,
                'description': response.message,
                'is_admin_response': True,
                'response_type': response.response_type
            })
        # Sort timeline by date
        timeline.sort(key=lambda x: x['date'])
            
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found in details page")
        messages.error(request, "Order Not found.")
        return redirect('my_orders')
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'order_details.html', context)

@login_required
def cancel_order(request, order_id):
    if request.method != 'POST':
        logger.error("Invalid request method for cancel_order")
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
        
    try:
        with transaction.atomic():  # Use transaction to ensure data consistency
            order = Order.objects.select_related('user').prefetch_related(
                'order_items',
                'order_items__variant',
                'order_items__size'
            ).get(id=order_id, user=request.user)
            
            # Check if order is already cancelled
            if order.order_status == 'CANCELLED':
                logger.warning(f"Order {order_id} is already cancelled")
                return JsonResponse({
                    'success': False, 
                    'message': 'Order is already cancelled'
                })
            
            # Check if order can be cancelled (e.g., not already shipped)
            if order.order_status not in ['PENDING', 'PROCESSING', 'SHIPPED']:
                logger.warning(f"Cannot cancel order {order_id} with status {order.order_status}")
                return JsonResponse({
                    'success': False, 
                    'message': f'Cannot cancel order with status {order.order_status}'
                })
            
            reason = data.get('reason', '')
            
            # Restore stock for each order item
            for order_item in order.order_items.all():
                try:
                    # Get the size object associated with this order item
                    size = order_item.size
                    if size:
                        # Increase the stock
                        size.stock += order_item.quantity
                        size.save()
                        
                        logger.info(
                            f"Restored {order_item.quantity} items to stock for "
                            f"variant {order_item.variant.id}, size {size.name}"
                        )
                        
                        # Update order item status
                        order_item.status = 'CANCELLED'
                        order_item.save()
                        
                except Exception as e:
                    logger.error(
                        f"Error restoring stock for order item {order_item.id}: {str(e)}"
                    )
                    raise  # Re-raise the exception to trigger rollback
            
            # Update order status and save cancellation reason
            order.order_status = 'CANCELLED'
            order.cancellation_reason = reason
            order.cancelled_at = timezone.now()
            order.save()
            
            logger.info(f"Successfully cancelled order {order_id}")
            return JsonResponse({
                'success': True,
                'message': 'Order cancelled successfully'
            })
            
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for user {request.user.id}")
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        })
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while cancelling the order'
        })

@login_required
@require_POST
def cancel_order_item(request, item_id):
    try:
        order_item = get_object_or_404(OrderItem, id=item_id)
        order = order_item.order
        
        # Verify ownership and status
        if order.user != request.user:
            return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
            
        if order_item.status not in ['PROCESSING', 'SHIPPED']:
            return JsonResponse({'success': False, 'message': 'Item cannot be cancelled'})
        
        with transaction.atomic():
            # Update item status
            order_item.status = 'CANCELLED'
            order_item.cancelled_at = timezone.now()
            order_item.save()
            
            # Restore stock if size exists
            if order_item.size:
                order_item.size.stock += order_item.quantity
                order_item.size.save()
            
            # Recalculate order total
            active_items = order.order_items.exclude(status__in=['CANCELLED', 'RETURNED'])
            new_total = sum(item.price * item.quantity for item in active_items)
            order.total_amount = new_total
            order.save()
            
            # If payment was made, add to wallet
            if order.payment_status == 'PAID':
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                refund_amount = order_item.price * order_item.quantity
                
                wallet.balance += refund_amount
                wallet.save()
                
                # Record transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    transaction_type='REFUND',
                    description=f'Refund for cancelled item #{order_item.id}'
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Item cancelled successfully'
            })
            
    except OrderItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order item not found'
        })
    except Exception as e:
        logger.error(f"Error cancelling order item {item_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while cancelling the item'
        })

@login_required
@require_POST
def return_order_item(request, item_id):
    try:
        data = json.loads(request.body)
        reason = data.get('reason')
        description = data.get('description')
        
        if not reason:
            return JsonResponse({
                'success': False,
                'message': 'Return reason is required'
            })
            
        order_item = get_object_or_404(OrderItem, id=item_id)
        
        # Verify ownership and status
        if order_item.order.user != request.user:
            return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
            
        if order_item.status != 'DELIVERED':
            return JsonResponse({'success': False, 'message': 'Item cannot be returned'})
            
        if order_item.return_status != 'NOT_REQUESTED':
            return JsonResponse({'success': False, 'message': 'Return already requested'})
        
        # Create return request
        ReturnRequest.objects.create(
            order_item=order_item,
            user=request.user,
            reason=reason,
            description=description
        )
        
        # Update order item status
        order_item.return_status = 'REQUESTED'
        order_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Return request submitted successfully'
        })
        
    except OrderItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order item not found'
        })
    except Exception as e:
        logger.error(f"Error processing return request for item {item_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your return request'
        })
            
        # Check if all items are cancelled
        if not active_items.exists():
            order.order_status = 'CANCELLED'
            order.save()
    
        return JsonResponse({
            'success': True,
            'new_total': float(new_total),
            'refund_amount': float(refund_amount) if order.payment_status == 'PAID' else 0
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_POST
def create_return_request(request, item_id):
    try:
        with transaction.atomic():
            data = json.loads(request.body)
            order_item = get_object_or_404(OrderItem, id=item_id)
            

            # Verify ownership and eligibility
            if order_item.order.user != request.user:
                return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
            
            if not order_item.can_return():
                return JsonResponse({
                    'success': False, 
                    'message': 'Item is not eligible for return'
                })
            
            # Check if return already requested
            if order_item.return_status != 'NOT_REQUESTED':
                return JsonResponse({
                    'success': False, 
                    'message': 'Return already requested for this item'
                })

            
            # Create return request
            return_request = ReturnRequest.objects.create(
                order_item=order_item,
                user=request.user,
                reason=data.get('reason'),
                description=data.get('description'),

                status='PENDING'
            )
            
            # Update order item status
            order_item.return_status = 'REQUESTED'
            order_item.save()
            
            # Send notification to admin
            # notify_admin_return_request(return_request)  # Implement this utility function
            
            return JsonResponse({
                'success': True,
                'message': 'Return request created successfully'
            })
            
    except Exception as e:
        logger.error(f"Error creating return request: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'An error occurred while processing your request'
        })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('payment_method')
        .prefetch_related(
            'order_items',
            'order_items__product',
            'order_items__variant',
            'order_items__variant__images',
            'order_items__size'
        ),
        id=order_id,
        user=request.user
    )
    
    # Prepare items with return eligibility
    items_data = []
    for item in order.order_items.all():
        item_data = {
            'id': item.id,
            'product_name': item.product.name if item.product else 'Product Unavailable',
            'variant_color': item.variant.color if item.variant else 'Color Unavailable',
            'size': item.size.name if item.size else None,
            'quantity': item.quantity,
            'price': item.price,
            'status': item.status,
            'return_status': item.return_status,
            'can_return': item.can_return() if hasattr(item, 'can_return') else False,
            'image_url': item.variant.images.first().image.url if (item.variant and item.variant.images.exists()) else None,
            'tracking_number': order.tracking_number if item.status == 'SHIPPED' else None,
            'delivered_at': item.delivered_at,
        }
        items_data.append(item_data)
    
    context = {
        'order': order,
        'items': items_data,
    }
    
    return render(request, 'order_detail.html', context)

@login_required
def order_details(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('payment_method')
        .prefetch_related(
            'order_items',
            'order_items__product',
            'order_items__variant',
            'order_items__variant__images',
            'order_items__size'
        ),
        order_id=order_id,
        user=request.user
    )
    
    # Prepare timeline events
    timeline = []
    
    # Order Placed (Always shown)
    timeline.append({
        'status': 'Order Placed',
        'date': order.created_at,
        'description': f'Order #{order.order_id} has been placed successfully'
    })
    
    # Processing
    if order.processed_at:
        timeline.append({
            'status': 'Processing',
            'date': order.processed_at,
            'description': 'Your order is being prepared for shipping'
        })
    
    # Shipped
    if order.shipped_at:
        timeline.append({
            'status': 'Shipped',
            'date': order.shipped_at,
            'description': f'Your order has been shipped via {order.shipping_carrier}. Tracking number: {order.tracking_number}'
        })
    
    # Delivered
    if order.delivered_at:
        timeline.append({
            'status': 'Delivered',
            'date': order.delivered_at,
            'description': 'Your order has been delivered successfully'
        })
    
    timeline.sort(key=lambda x: x['date'])
    
    # Prepare items with return eligibility
    items_data = []
    for item in order.order_items.all():
        item_data = {
            'id': item.id,
            'product_name': item.product.name if item.product else 'Product Unavailable',
            'variant_color': item.variant.color if item.variant else 'Color Unavailable',
            'size': item.size.name if item.size else None,
            'quantity': item.quantity,
            'price': item.price,
            'status': item.status,
            'return_status': item.return_status,
            'can_return': item.can_return() if hasattr(item, 'can_return') else False,
            'image_url': item.variant.images.first().image.url if (item.variant and item.variant.images.exists()) else None,
            'tracking_number': order.tracking_number if item.status == 'SHIPPED' else None,
            'delivered_at': item.delivered_at,
        }
        items_data.append(item_data)
    
    context = {
        'order': order,
        'items': items_data,
        'timeline': timeline,
    }
    
    return render(request, 'order_details.html', context)
    
            
def available_coupons(request):
    today = timezone.now().date()
    coupons = Coupon.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )
    
    # Get cart total if exists
    cart = None
    cart_total = 0
    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
        if cart:
            cart_total = cart.total_price
    
    coupon_data = []
    for coupon in coupons:
        # Check if coupon is applicable based on cart total
        is_applicable = cart_total >= coupon.minimum_purchase if cart else False
        
        # Calculate amount needed to use coupon
        amount_needed = coupon.minimum_purchase - cart_total if cart_total < coupon.minimum_purchase else 0
        
        # Format discount text based on type
        if coupon.type == 'percentage':
            discount_text = f"{int(coupon.value)}% OFF"
        else:
            discount_text = f"₹{int(coupon.value)} OFF"
            
        coupon_data.append({
            'code': coupon.code,
            'discount_text': discount_text,
            'minimum_purchase': coupon.minimum_purchase,
            'is_applicable': is_applicable,
            'expiry_date': coupon.end_date,
            'amount_needed': amount_needed  # Add this field
        })
    
    return render(request, 'available_coupons.html', {
        'coupons': coupon_data,
        'cart_total': cart_total
    })
@login_required
@require_POST
def apply_coupon(request):
    """Apply a coupon to the cart with improved validation and error handling"""
    if request.method == 'POST':
        try:
            # Get the coupon code from the request
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            
            # Log the received data for debugging
            logger.debug(f"Coupon code received: {code}")
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'message': 'Please provide a coupon code'
                })
            
            # Get the user's active cart
            cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
            if not cart:
                return JsonResponse({
                    'success': False,
                    'message': 'No active cart found'
                })
            
            # Check if cart has items
            if not cart.items.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Your cart is empty'
                })
            
            # Check if coupon exists and is valid - case insensitive search
            try:
                # Try to find the coupon with case-insensitive search
                coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
                if not coupon:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid coupon code'
                    })
            except Exception as e:
                logger.error(f"Error finding coupon: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid coupon code'
                })
            
            # Check if coupon is expired
            today = timezone.now().date()
            if coupon.end_date and coupon.end_date < today:
                return JsonResponse({
                    'success': False,
                    'message': 'This coupon has expired'
                })
                
            # Check if coupon is not yet valid
            if coupon.start_date and coupon.start_date > today:
                return JsonResponse({
                    'success': False,
                    'message': f'This coupon is valid from {coupon.start_date.strftime("%d %b %Y")}'
                })
            
            # Check how many times the user has used this coupon
            user_usage_count = CouponUsage.objects.filter(user=request.user, coupon=coupon).count()
            
            # Log current usage vs limit for debugging
            logger.info(f"Coupon {coupon.code} (ID: {coupon.id}): user_usage_count={user_usage_count}, usage_limit={coupon.usage_limit}, user_id={request.user.id}")
            
            # Check if user has reached their personal usage limit for this coupon
            if user_usage_count >= coupon.usage_limit:
                logger.warning(f"User {request.user.id} has exceeded usage limit for coupon {coupon.code}. Used {user_usage_count} times, limit is {coupon.usage_limit}")
                return JsonResponse({
                    'success': False,
                    'message': f'You have already used this coupon the maximum number of times. Used: {user_usage_count}/{coupon.usage_limit}'
                })
                
            # Log the usage count for debugging
            logger.info(f"User {request.user.id} has used coupon {coupon.code} {user_usage_count} times out of {coupon.usage_limit}")
            
            # Check minimum cart value if applicable
            cart_total = cart.total_price
            if coupon.minimum_purchase and cart_total < coupon.minimum_purchase:
                return JsonResponse({
                    'success': False,
                    'message': f'Minimum cart value of ₹{coupon.minimum_purchase} required (current: ₹{cart_total})'
                })
            
            # Check total usage limit across all users if applicable
            total_usage_count = CouponUsage.objects.filter(coupon=coupon).count()
            
            # Log the total usage count for debugging
            logger.info(f"Coupon {coupon.code} has been used {total_usage_count} times in total")
            
            # This check is for a global usage limit, which we'll keep separate from per-user limit
            # We're assuming the usage_limit field is for per-user limit as per your requirement
                
            # Remove any existing coupon before applying new one
            if cart.coupon:
                cart.coupon = None
                cart.save()
            
            # Apply coupon to cart
            cart.coupon = coupon
            cart.save()
            
            # Note: We don't create a CouponUsage record here because that should only happen
            # when the order is actually placed, not just when applying to the cart
            
            # Calculate all totals
            subtotal = cart.total_price
            coupon_discount = cart.calculate_coupon_discount()
            delivery_charge = 0.00  # Free delivery
            final_price = cart.final_price
            
            coupon_description = ''
            if coupon.type == 'percentage':
                coupon_description = f'{coupon.value}% off on your order'
            else:
                coupon_description = f'₹{coupon.value} off on your order'
            
            return JsonResponse({
                'success': True,
                'coupon': {
                    'code': coupon.code,
                    'type': coupon.type,
                    'value': float(coupon.value),
                    'description': coupon_description
                },
                'subtotal': float(subtotal),
                'discount': float(coupon_discount),
                'delivery_charge': float(delivery_charge),
                'final_amount': float(final_price),
                'message': 'Coupon applied successfully!'
            })
            
        except Exception as e:
            logger.error(f"Error applying coupon: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'Failed to apply coupon. Please try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def check_coupon(request):
    """Check if the user has an active coupon applied to their cart"""
    if request.method == 'GET':
        try:
            # Get the user's active cart
            cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
            
            if not cart or not cart.coupon:
                return JsonResponse({
                    'success': True,
                    'has_coupon': False
                })
            
            # Get coupon details
            coupon = cart.coupon
            coupon_discount = cart.calculate_coupon_discount()
            
            return JsonResponse({
                'success': True,
                'has_coupon': True,
                'coupon_code': coupon.code,
                'description': f'{coupon.value}% off on your order',
                'discount': float(coupon_discount)
            })
            
        except Exception as e:
            logger.error(f"Error checking coupon: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'Failed to check coupon status'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_cart_totals(request):
    """Get updated cart totals including subtotal, discounts, and final amount"""
    if request.method == 'GET':
        try:
            # Get the user's active cart
            cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
            
            if not cart:
                return JsonResponse({
                    'success': False,
                    'message': 'No active cart found'
                })
            
            # Calculate all totals
            subtotal = cart.total_price
            coupon_discount = cart.calculate_coupon_discount() if cart.coupon else 0
            delivery_charge = 0.00  # Free delivery
            final_amount = cart.final_price
            
            return JsonResponse({
                'success': True,
                'subtotal': float(subtotal),
                'coupon_discount': float(coupon_discount),
                'delivery_charge': float(delivery_charge),
                'final_amount': float(final_amount)
            })
            
        except Exception as e:
            logger.error(f"Error getting cart totals: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'Failed to get cart totals'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def remove_coupon(request):
    """Remove coupon from the cart"""
    if request.method == 'POST':
        try:
            # Get the user's active cart
            cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
            
            if not cart:
                return JsonResponse({
                    'success': False,
                    'message': 'No active cart found'
                })
            
            # Check if cart has a coupon
            if not cart.coupon:
                return JsonResponse({
                    'success': False,
                    'message': 'No coupon applied to remove'
                })
            
            # Remove coupon
            cart.coupon = None
            cart.save()
            
            # Calculate updated totals
            subtotal = cart.total_price
            delivery_charge = 0.00  # Free delivery
            final_price = cart.final_price
            
            return JsonResponse({
                'success': True,
                'subtotal': float(subtotal),
                'delivery_charge': float(delivery_charge),
                'final_amount': float(final_price),
                'message': 'Coupon removed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error removing coupon: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'Failed to remove coupon. Please try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@require_POST
def create_order(request):
    """Create a new order from the checkout page"""
    try:
        # Parse request data
        data = json.loads(request.body)
        address_id = data.get('address_id')
        payment_method = data.get('payment_method')
        
        # Validate input
        if not address_id:
            return JsonResponse({
                'success': False,
                'message': 'Please select a delivery address'
            })
            
        if not payment_method:
            return JsonResponse({
                'success': False,
                'message': 'Please select a payment method'
            })
            
        # Get user's active cart
        cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
        if not cart or not cart.items.exists():
            return JsonResponse({
                'success': False,
                'message': 'Your cart is empty'
            })
            
        # Get the selected address
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Selected address not found'
            })
            
        # Create the order
        with transaction.atomic():
            # Generate order number
            order_number = f'ORD-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}'
            
            # Calculate totals
            cart_items = cart.items.all()
            subtotal = cart.total_price
            
            # Calculate product discount (includes all offers)
            product_discount = Decimal(str(sum(
                (item.variant.price - item.variant.final_price) * item.quantity
                for item in cart_items
                if item.variant.final_price < item.variant.price
            )))
            
            coupon_discount = cart.calculate_coupon_discount() if cart.coupon else 0
            delivery_charge = 0  # Free delivery
            final_amount = cart.final_price
            
            # Get or create payment method
            payment_method_obj, _ = PaymentMethod.objects.get_or_create(name=payment_method)

            # Create order object
            order = Order.objects.create(
                user=request.user,
                # Use address fields from the address object
                full_name=address.full_name,
                email=address.email,
                phone=address.phone,
                address_line1=address.address_line1,
                address_line2=address.address_line2,
                city=address.city,
                state=address.state,
                pincode=address.pincode,
                # Other order fields
                payment_method=payment_method_obj,
                total_amount=final_amount,
                product_discount=product_discount,
                coupon_discount=coupon_discount,
                order_status='PENDING',
                payment_status='PENDING'
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.variant.product,
                    variant=cart_item.variant,
                    quantity=cart_item.quantity,
                    price=cart_item.variant.final_price or cart_item.variant.price,  # Price paid
                    original_price=cart_item.variant.price,  # MRP
                    size=cart_item.size
                )
                # Only reduce stock for COD orders here. For Razorpay, do it after payment success.
                if payment_method != 'razorpay':
                    size = cart_item.size
                    if size:
                        if size.stock >= cart_item.quantity:
                            size.stock -= cart_item.quantity
                            size.save()
                        else:
                            return JsonResponse({
                                'success': False,
                                'message': f'Insufficient stock for {cart_item.variant.product.name} in size {size.name}. Only {size.stock} available.'
                            })
            
            # If there was a coupon, record its usage
            if cart.coupon:
                CouponUsage.objects.create(
                    coupon=cart.coupon,
                    user=request.user,
                    order=order
                )
            
            # For Razorpay payments, we'll mark the cart as ordered only after successful payment
            # For COD, we can mark it as ordered immediately
            if payment_method != 'razorpay':
                # Mark cart as ordered
                cart.is_ordered = True
                cart.save()
                
                # Create new empty cart for user
                new_cart = Cart.objects.create(user=request.user)
            else:
                # For Razorpay, store the order ID in the session for recovery
                if 'pending_orders' not in request.session:
                    request.session['pending_orders'] = []
                
                # Add this order to pending orders if not already there
                pending_orders = request.session['pending_orders']
                if order.order_id not in pending_orders:
                    pending_orders.append(order.order_id)
                    request.session['pending_orders'] = pending_orders
                    request.session.modified = True
            
            # Return appropriate response based on payment method
            if payment_method == 'razorpay':
                # Set payment expiry time to 10 minutes from now
                order.payment_expiry_time = timezone.now() + timezone.timedelta(minutes=10)
                order.save()
                # Create Razorpay order
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                payment_data = {
                    'amount': int(final_amount * 100),  # Amount in paise
                    'currency': 'INR',
                    'receipt': order_number,
                    'payment_capture': 1  # Auto-capture
                }
                
                try:
                    # Log the payment data for debugging
                    logger.info(f"Creating Razorpay order with data: {payment_data}")
                    
                    # Ensure Razorpay credentials are set
                    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                        logger.error("Razorpay credentials are not properly configured")
                        return JsonResponse({
                            'success': False,
                            'message': 'Payment gateway configuration error. Please contact support.'
                        })
                    
                    # Create Razorpay order
                    razorpay_order = client.order.create(payment_data)
                    logger.info(f"Razorpay order created successfully: {razorpay_order['id']}")
                    
                    # Update order with Razorpay order ID
                    order.razorpay_order_id = razorpay_order['id']
                    order.save()
                    
                    return JsonResponse({
                        'success': True,
                        'payment_required': True,
                        'order_id': order.id,
                        'razorpay_order_id': razorpay_order['id'],
                        'amount': final_amount,
                        'key_id': settings.RAZORPAY_KEY_ID,
                        'customer_name': f'{request.user.first_name} {request.user.last_name}'.strip() or request.user.username,
                        'customer_email': request.user.email,
                        'customer_phone': request.user.phone or ''
                    })
                except Exception as e:
                    logger.error(f'Razorpay error: {str(e)}', exc_info=True)
                    return JsonResponse({
                        'success': False,
                        'message': 'Payment gateway error. Please try again.'
                    })
            else:
                # COD order - no payment gateway needed
                return JsonResponse({
                    'success': True,
                    'payment_required': False,
                    'order_id': order.id,
                    'redirect_url': reverse('order_details', args=[order.order_id]),
                    'message': 'Order placed successfully!'
                })
                
    except Exception as e:
        logger.error(f'Error creating order: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your order. Please try again.'
        })

@login_required
def add_address_checkout(request):
    """Add a new address from the checkout page"""
    if request.method == 'POST':
        try:
            # Extract address data from form
            address_type = request.POST.get('address_type')
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address_line1 = request.POST.get('address_line1')
            address_line2 = request.POST.get('address_line2', '')
            city = request.POST.get('city')
            state = request.POST.get('state')
            pincode = request.POST.get('pincode')
            is_default = request.POST.get('is_default') == 'on'
            
            # Validate required fields
            if not all([address_type, full_name, email, phone, address_line1, city, state, pincode]):
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill all required fields',
                    'form_data': {
                        'address_type': address_type,
                        'full_name': full_name,
                        'email': email,
                        'phone': phone,
                        'address_line1': address_line1,
                        'address_line2': address_line2,
                        'city': city,
                        'state': state,
                        'pincode': pincode,
                        'is_default': is_default
                    }
                })
            
            # Create new address
            address = Address.objects.create(
                user=request.user,
                address_type=address_type,
                full_name=full_name,
                email=email,
                phone=phone,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                pincode=pincode,
                is_default=is_default
            )
            
            # If this is set as default, unset other default addresses
            if is_default:
                Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
            
            # Return success response with the new address ID
            return JsonResponse({
                'success': True,
                'message': 'Address added successfully',
                'address_id': address.id,
                'address_html': f'''
                <div class="flex">
                    <input type="radio" name="selected_address" id="address-{address.id}" value="{address.id}" checked class="mt-1 mr-4 text-[#ff6b00]">
                    <div class="flex-1 bg-zinc-800 p-4 rounded-lg">
                        <div class="flex justify-between mb-2">
                            <div class="flex items-center">
                                <span class="inline-block px-2 py-1 text-xs font-semibold bg-[#ff6b00]/20 text-[#ff6b00] rounded-md mr-2">{address.address_type}</span>
                                <span class="text-sm font-medium">{address.full_name}</span>
                            </div>
                        </div>
                        <div class="text-zinc-400 text-sm space-y-1">
                            <p>{address.address_line1}</p>
                            {f'<p>{address.address_line2}</p>' if address.address_line2 else ''}
                            <p>{address.city}, {address.state} - {address.pincode}</p>
                            <p>Phone: {address.phone}</p>
                        </div>
                    </div>
                </div>
                '''
            })
            
        except Exception as e:
            logger.error(f"Error adding address: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while adding the address'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def auto_cancel_expired_orders():
    """Utility function to cancel orders with expired payments"""
    try:
        # Find orders with expired payment time
        now = timezone.now()
        expired_orders = Order.objects.filter(
            payment_status__in=['PAYMENT_PENDING', 'FAILED'],
            payment_expiry_time__lt=now,
            order_status='PENDING'
        )
        
        count = 0
        for order in expired_orders:
            # Cancel the order
            order.order_status = 'CANCELLED'
            order.cancelled_at = now
            order.payment_failure_reason = 'Payment time expired'
            order.save()
            
            # Create status history entry
            OrderStatusHistory.objects.create(
                order=order,
                old_status='PENDING',
                new_status='CANCELLED',
                reason='Payment time expired'
            )
            count += 1
        
        if count > 0:
            logger.info(f"Auto-cancelled {count} orders with expired payments")
        
        return count
    except Exception as e:
        logger.error(f"Error in auto_cancel_expired_orders: {str(e)}", exc_info=True)
        return 0

@login_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    
    context = {
        'wallet': wallet,
        'transactions': transactions
    }
    return render(request, 'wallet.html', context)