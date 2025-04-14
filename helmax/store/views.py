from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate,logout as auth_logout
from django.contrib import messages
from django.utils.timezone import now
from manager.forms import SignupForm, OTPVerificationForm, PasswordResetRequestForm,SetPasswordForm
from .forms import AddressForm
from django.http import Http404
from django.conf import settings
import os
from .invoice_generator import generate_invoice_pdf
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
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
import logging
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.http import  JsonResponse, HttpResponse
import json
from django.conf import settings
from django.apps import apps
from .utils import send_otp_email
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
import logging  
from django.db.models import Sum, F, Count
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
    products = (
        Product.objects.filter(is_active=True)
        .prefetch_related('variants', 'variants__images')
        .select_related('category', 'brand')
    )[:10]  

    # product_data = []
    # for product in products:
    #     primary_variant = product.variants.first()
    #     if primary_variant:
    #         primary_image = primary_variant.images.filter(is_primary=True).first()
    #         print(primary_variant)  # Check if primary_variant is correctly fetched
    #         print(primary_image) 
    #         product_data.append({
    #             'id': product.id,
    #             'name': product.name,
    #             'description': product.description,
    #             'price': primary_variant.discount_price or primary_variant.price,
    #             'image_url': primary_image.image.url if primary_image else 'default_image.jpg',
    #         })

    return render(request, 'home.html', {'products': products})


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
            'image_url': primary_image.image.url if primary_image and hasattr(primary_image, 'image') else '/static/images/placeholder.jpg',
            'total_stock': sum(size.stock for size in first_variant.sizes.all()) if first_variant.sizes.exists() else 0,
            'discount_percentage': int(((first_variant.price - first_variant.discount_price) / first_variant.price) * 100) if first_variant.discount_price and first_variant.price and first_variant.discount_price < first_variant.price else 0
        })

    return JsonResponse({
        'products': product_data
    })


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
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
                return redirect('signup')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})





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
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user,backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'login.html')

    if request.user.is_authenticated:
        return redirect('home')
    
    return render(request, 'login.html')



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

def get_variant_data(request, product_id, variant_id):
    variant = get_object_or_404(
        Variant.objects.select_related('product')
        .prefetch_related('images', 'sizes'),
        product_id=product_id,
        id=variant_id,
        is_active=True
    )
    
    # Get primary image, with fallback
    primary_image = variant.images.filter(is_primary=True).first()
    if not primary_image:
        primary_image = variant.images.first()
    
    data = {
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
    # Get all active categories and brands for filters
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    # Get initial products with their first active variant and image
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).select_related(
        'category', 
        'brand'
    ).prefetch_related(
        'variants',
        'variants__images',
        'variants__sizes'
    ).distinct()
    
    # Apply filters if provided
    categories_filter = request.GET.get('categories')
    brands_filter = request.GET.get('brands')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_option = request.GET.get('sort', 'new_arrivals')
    
    if categories_filter:
        category_ids = categories_filter.split(',')
        products = products.filter(category_id__in=category_ids)
    
    if brands_filter:
        brand_ids = brands_filter.split(',')
        products = products.filter(brand_id__in=brand_ids)
    
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
    
    # Apply sorting
    if sort_option == 'price_low_high':
        products = products.order_by('variants__price')
    elif sort_option == 'price_high_low':
        products = products.order_by('-variants__price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    else:  # Default to newest
        products = products.order_by('-id')

    # Prepare product data for template
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

        # Calculate total stock safely
        total_stock = 0
        try:
            for variant in product.variants.filter(is_active=True):
                for size in variant.sizes.all():
                    total_stock += size.stock
        except Exception:
            # Fallback if size or stock doesn't exist
            pass

        # Calculate discount percentage if applicable
        discount_percentage = 0
        if first_variant.discount_price and first_variant.price and first_variant.price > 0:
            discount_percentage = int(
                ((first_variant.price - first_variant.discount_price) / first_variant.price) * 100
            )

        # Check if brand exists
        brand_name = product.brand.name if product.brand else "No Brand"
        
        # Check if category exists
        category_name = product.category.name if product.category else "Uncategorized"
        
        # Get description
        description = product.description if hasattr(product, 'description') else ""

        # Add product only if it has valid data
        product_data.append({
            'id': product.id,
            'name': product.name,
            'description': description,
            'price': first_variant.price or 0,
            'discount_price': first_variant.discount_price or first_variant.price or 0,
            'image_url': primary_image.image.url if primary_image and hasattr(primary_image, 'image') else '/static/images/placeholder.jpg',
            'total_stock': total_stock,
            'discount_percentage': discount_percentage,
            'category': category_name,
            'brand': brand_name,
        })

    # Pagination
    paginator = Paginator(product_data, 8)  # 12 products per page
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.get_page(page)
    except (PageNotAnInteger, EmptyPage):
        products_page = paginator.get_page(1)
    
    context = {
        'products': products_page,
        'categories': categories,
        'brands': brands
    }
    
    return render(request, 'product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand')
        .prefetch_related(
            Prefetch('variants', 
                queryset=Variant.objects.filter(is_active=True).prefetch_related(
                    'sizes',
                    Prefetch('images', queryset=ProductImage.objects.all())  # Remove filter to get all images
                )
            )
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
    }
    
    return render(request, 'product_details.html', context)
######### CART ########




def view_cart(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login to access Cart")
        return redirect('Login')  # Redirect to login page if user is not authenticated
 

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

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.total_price,
        'total_discount': cart.total_discount,
        'final_price': cart.final_price
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
            size = Size.objects.get(name=size_name, product_variant=variant)
        except (Variant.DoesNotExist, Size.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Product variant or size not found'}, status=404)

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
    


@login_required
def wishlist_view(request):
    try:
        # Get or create single wishlist for user
        wishlist = Wishlist.get_or_create_wishlist(request.user)
        
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
            # Get primary image or first image
            primary_image = variant.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = variant.images.first()

            items_data.append({
                'id': variant.id,
                'product_name': variant.product.name,
                'color': variant.color,
                'price': variant.price,
                'discount_price': variant.discount_price,
                'image_url': primary_image.image.url if primary_image else None,
                'stock': sum(size.stock for size in variant.sizes.all())
            })
            
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
                # Get first active variant
                first_variant = product.variants.filter(is_active=True).first()
                if first_variant:
                    # Get primary image or first image
                    primary_image = first_variant.images.filter(is_primary=True).first()
                    if not primary_image:
                        primary_image = first_variant.images.first()
                    
                    similar_products.append({
                        'id': product.id,
                        'name': product.name,
                        'price': first_variant.price,
                        'discount_price': first_variant.discount_price,
                        'image_url': primary_image.image.url if primary_image else None
                    })

        return render(request, 'wishlist.html', {
            'wishlist_items': items_data,
            'similar_products': similar_products
        })
        
    except Exception as e:
        messages.error(request, "Error loading wishlist")
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
        wishlist = Wishlist.get_or_create_wishlist(request.user)
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
        wishlist = Wishlist.get_or_create_wishlist(request.user)
        wishlist.variants.add(variant)
        return JsonResponse({'success': True, 'message': 'Added to wishlist!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error adding to wishlist'})

@login_required
def sort_wishlist(request, sort_by):
    """Sort wishlist items"""
    try:
        wishlist = Wishlist.get_or_create_wishlist(request.user)
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
        
        items_data = [{
            'id': item.id,
            'product_name': item.product.name,
            'color': item.color,
            'price': item.price,
            'discount_price': item.discount_price,
            'image_url': item.images.filter(is_primary=True).first().image.url if item.images.filter(is_primary=True).exists() else item.images.first().image.url if item.images.exists() else None,
            'stock': sum(size.stock for size in item.sizes.all())
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
        wishlist = Wishlist.get_or_create_wishlist(request.user)
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
        wishlist = Wishlist.get_or_create_wishlist(request.user)
        wishlist.variants.clear()
        return JsonResponse({'success': True, 'message': 'Wishlist cleared successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error clearing wishlist'})

@login_required
@require_POST
def add_multiple_to_cart(request):
    """Add multiple wishlist items to cart"""
    try:
        data = json.loads(request.body)
        variant_ids = data.get('variant_ids', [])
        
        if not variant_ids:
            return JsonResponse({'success': False, 'message': 'No items selected'})
        
        cart = Cart.objects.get_or_create(user=request.user)[0]
        added_count = 0
        
        for variant_id in variant_ids:
            try:
                variant = Variant.objects.get(id=variant_id, is_active=True)
                # Check if variant has stock
                if sum(size.stock for size in variant.sizes.all()) > 0:
                    # Get first size with stock
                    size = next((s for s in variant.sizes.all() if s.stock > 0), None)
                    if size:
                        cart_item, created = CartItem.objects.get_or_create(
                            cart=cart,
                            variant=variant,
                            size=size,
                            defaults={'quantity': 1}
                        )
                        if not created:
                            cart_item.quantity += 1
                            cart_item.save()
                        added_count += 1
            except Variant.DoesNotExist:
                continue
        
        if added_count > 0:
            return JsonResponse({
                'success': True, 
                'message': f'{added_count} item(s) added to cart',
                'cart_count': CartItem.objects.filter(cart=cart).count()
            })
        else:
            return JsonResponse({'success': False, 'message': 'No items could be added to cart'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error adding items to cart'})



import re
####### profile ##########
@login_required(login_url='userlogin')
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
        user.full_name = full_name
        user.phone = phone
        user.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('user_profile', user_id=user.id)
    
    # GET request
    context = {
        'user': user,
        'full_name': user.full_name or user.get_full_name(),
        'email': user.email,
        'phone': user.phone or '',
        'referral_code': user.referral_code or 'N/A',
    }
    return render(request, 'profile.html', context)




################## Addresss ####################


@never_cache
@login_required(login_url='userlogin')
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
                    'message': str(e)
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data',
                'errors': form.errors
            })

    context = {
        'addresses': user_addresses,
    }
    return render(request, 'usermanageaddress.html', context)

@login_required(login_url='userlogin')
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

@login_required(login_url='userlogin')
@never_cache
def deleteAddress(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_deleted = True
    address.save()
    return JsonResponse({'success': True, 'message': 'Address deleted successfully'})

@login_required(login_url='userlogin')
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

@login_required(login_url='userlogin')
@never_cache
def user_checkout(request):
    try:
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
                continue
                
            cart_items.append(item)
            total_quantity += item.quantity

        if not cart_items:
            messages.warning(request, "No valid items in cart")
            return redirect('view_cart')

        # Get addresses and payment methods
        user_addresses = Address.objects.filter(user=request.user, is_deleted=False)
        payment_methods = PaymentMethod.objects.all()

        # Calculate totals
        subtotal = cart.total_price
        product_discount = sum(
            (item.variant.price - item.variant.discount_price) * item.quantity
            for item in cart_items
            if item.variant.discount_price
        )
        coupon_discount = cart.calculate_coupon_discount()
        total_discount = product_discount + coupon_discount
        final_price = cart.final_price

        # Get available coupons
        today = timezone.now().date()
        coupons = Coupon.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
        
        coupon_data = []
        for coupon in coupons:
            is_applicable = cart.total_price >= coupon.minimum_purchase
            amount_needed = coupon.minimum_purchase - cart.total_price if cart.total_price < coupon.minimum_purchase else 0
            
            coupon_data.append({
                'code': coupon.code,
                'type': coupon.type,
                'value': coupon.value,
                'minimum_purchase': coupon.minimum_purchase,
                'is_applicable': is_applicable,
                'expiry_date': coupon.end_date,
                'amount_needed': amount_needed
            })

        context = {
            'user_addresses': user_addresses,
            'cart_items': cart_items,
            'payment_methods': payment_methods,
            'total_quantity': total_quantity,
            'subtotal': subtotal,
            'product_discount': product_discount,
            'coupon_discount': coupon_discount,
            'total_discount': total_discount,
            'final_price': final_price,
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
def place_order(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
        
    try:
        # Get form data
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')
        
        # Validate address
        if not address_id:
            return JsonResponse({'success': False, 'message': 'Please select a delivery address'})
            
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid address'})
            
        # Get cart
        try:
            cart = Cart.objects.get(user=request.user, is_ordered=False)
            if not cart.items.exists():
                return JsonResponse({'success': False, 'message': 'Your cart is empty'})
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No active cart found'})
            
        # Get or create payment methods
        cod_method, _ = PaymentMethod.objects.get_or_create(name='COD')
        razorpay_method, _ = PaymentMethod.objects.get_or_create(name='Razorpay')
        
        # Set payment method
        payment_method_obj = razorpay_method if payment_method == 'razorpay' else cod_method
        
        with transaction.atomic():
            # Calculate discounts
            product_discount = sum(
                (item.variant.price - item.variant.discount_price) * item.quantity
                for item in cart.items.all()
                if item.variant.discount_price
            )
            coupon_discount = cart.calculate_coupon_discount() if cart.coupon else 0
            total_discount = product_discount + coupon_discount
            
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.final_price,
                product_discount=product_discount,
                coupon_discount=coupon_discount,
                payment_method=payment_method_obj,
                full_name=address.full_name,
                email=address.email,
                phone=address.phone,
                address_line1=address.address_line1,
                address_line2=address.address_line2,
                city=address.city,
                state=address.state,
                pincode=address.pincode
            )
            
            # Create order items and update stock
            for cart_item in cart.items.all():
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.variant.product,
                    variant=cart_item.variant,
                    size=cart_item.size,
                    quantity=cart_item.quantity,
                    price=cart_item.variant.discount_price or cart_item.variant.price
                )
                
                # Update stock
                size = cart_item.size
                if size.stock < cart_item.quantity:
                    raise ValueError(f'Insufficient stock for {cart_item.variant.product.name}')
                size.stock -= cart_item.quantity
                size.save()
            
            # IMPORTANT: Clear cart items - this is the key fix
            CartItem.objects.filter(cart=cart).delete()
            
            # Mark cart as ordered
            cart.is_ordered = True
            cart.save()
            
            # Handle payment method specific logic
            if payment_method == 'razorpay':
                try:
                    import razorpay
                    
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    amount_in_paise = int(float(order.total_amount) * 100)
                    razorpay_order = client.order.create({
                        "amount": amount_in_paise,
                        "currency": "INR",
                        "receipt": f"order_{order.id}",
                        "payment_capture": "1"
                    })
                    order.razorpay_order_id = razorpay_order['id']
                    order.save()
                    
                    return JsonResponse({
                        'success': True,
                        'razorpay_order_id': razorpay_order['id'],
                        'amount': amount_in_paise,
                        'key_id': settings.RAZORPAY_KEY_ID
                    })
                except Exception as e:
                    logger.error(f"Razorpay error: {str(e)}")
                    raise ValueError(f'Failed to create Razorpay order: {str(e)}')
            else:
                # For COD orders, just redirect to confirmation
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('order_details', args=[order.order_id])
                })
                
    except ValueError as e:
        return JsonResponse({'success': False, 'message': str(e)})
    except Exception as e:
        logger.error(f"Error in place_order: {str(e)}")
        return JsonResponse({'success': False, 'message': f'An unexpected error occurred: {str(e)}'})

@csrf_exempt
@login_required
def download_invoice(request, order_id):
    try:
        # Get the order and verify ownership
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Generate the invoice PDF
        filename = generate_invoice_pdf(order)
        
        # Prepare the file path
        file_path = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        
        raise Http404()
        
    except Exception as e:
        raise Http404(str(e))

def payment_success(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)

            try:
                # Verify payment signature
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })
                
                # Update order status for successful payment
                order.payment_status = 'PAID'
                order.razorpay_payment_id = razorpay_payment_id
                order.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment successful',
                    'redirect_url': reverse('order_details', args=[order.order_id])
                })

            except Exception as e:
                # Payment verification failed - update order status
                order.payment_status = 'FAILED'
                order.payment_failure_reason = str(e)
                order.payment_attempts += 1
                order.last_payment_attempt = timezone.now()
                order.save()

                # Still redirect to order details, but with error status
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment verification failed. You can retry payment from order details.',
                    'redirect_url': reverse('order_details', args=[order.order_id])
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
def retry_payment(request, order_id):
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        
        if order.payment_status == 'PAID':
            return JsonResponse({
                'status': 'error',
                'message': 'Order is already paid'
            })

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create new Razorpay order
        payment = client.order.create({
            'amount': int(order.total_amount * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1
        })
        
        # Update order with new Razorpay order ID
        order.razorpay_order_id = payment['id']
        order.payment_status = 'PAYMENT_PENDING'
        order.save()
        
        return JsonResponse({
            'status': 'success',
            'order_id': payment['id'],
            'amount': int(order.total_amount * 100),
            'key': settings.RAZORPAY_KEY_ID
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





################# Order ####################
from manager.models import Order, OrderItem, Cart, CartItem
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

@login_required(login_url='userlogin')
def order_details(request, order_id):
    try:
        order = get_object_or_404(
            Order.objects.prefetch_related(
                'order_items',
                'order_items__product',
                'order_items__variant',
                'order_items__variant__images',
                'order_items__size' 
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
            'product_name': item.product.name,
            'variant_color': item.variant.color,
            'size': item.size.name if item.size else None,
            'quantity': item.quantity,
            'price': item.price,
            'status': item.status,
            'return_status': item.return_status,
            'can_return': item.can_return(),
            'image_url': item.variant.images.first().image.url if item.variant.images.exists() else None,
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
            'product_name': item.product.name,
            'variant_color': item.variant.color,
            'size': item.size.name if item.size else None,
            'quantity': item.quantity,
            'price': item.price,
            'status': item.status,
            'return_status': item.return_status,
            'can_return': item.can_return(),
            'image_url': item.variant.images.first().image.url if item.variant.images.exists() else None,
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
def apply_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('coupon_code')
            
            cart = Cart.objects.get(user=request.user, is_ordered=False)
            
            try:
                coupon = Coupon.objects.get(
                    code=code,
                    is_active=True,
                    start_date__lte=timezone.now().date(),
                    end_date__gte=timezone.now().date()
                )
                
                # Check minimum purchase
                if cart.total_price < coupon.minimum_purchase:
                    return JsonResponse({
                        'success': False,
                        'message': f'Minimum purchase amount of ₹{coupon.minimum_purchase} required'
                    })
                
                # Check usage limit
                usage_count = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
                if usage_count >= coupon.usage_limit:
                    return JsonResponse({
                        'success': False,
                        'message': 'Coupon usage limit exceeded'
                    })
                
                # Apply coupon to cart
                cart.coupon = coupon
                cart.save()
                
                return JsonResponse({
                    'success': True,
                    'discount': float(cart.calculate_coupon_discount()),
                    'final_amount': float(cart.final_price),
                    'message': 'Coupon applied successfully!'
                })
                
            except Coupon.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid coupon code'
                })
                
        except Exception as e:

            print(f"Payment verification failed with error: {str(e)}")

            return JsonResponse({
                'success': False,
                'message': str(e)
            })
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def wallet_view(request):
    """View to display user's wallet and transaction history"""
    try:
        # Get or create wallet for user
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # Get all transactions with related orders
        transactions = WalletTransaction.objects.filter(wallet=wallet)\
            .select_related('order')\
            .order_by('-created_at')

        # Prepare transaction data
        transaction_data = []
        for transaction in transactions:
            data = {
                'id': transaction.id,
                'amount': transaction.amount,
                'type': transaction.transaction_type,
                'description': transaction.description,
                'date': transaction.created_at,
                'status': transaction.status,
                'order_number': transaction.order.order_number if transaction.order else None
            }
            transaction_data.append(data)

        context = {
            'wallet': wallet,
            'transactions': transaction_data,
            'total_credits': sum(t.amount for t in transactions if t.transaction_type in ['CREDIT', 'REFUND']),
            'total_debits': sum(t.amount for t in transactions if t.transaction_type == 'DEBIT'),
        }
        
        return render(request, 'wallet.html', context)
        
    except Exception as e:
        logger.error(f"Error in wallet view: {str(e)}")
        messages.error(request, "An error occurred while loading your wallet.")
        return redirect('home')

def get_product_details(request, variant_id):
    try:
        variant = get_object_or_404(
            Variant.objects.select_related('product')
            .prefetch_related('images', 'sizes'),
            id=variant_id,
            is_active=True,
            product__is_active=True
        )
        
        # Get primary image or first image
        primary_image = variant.images.filter(is_primary=True).first()
        if not primary_image:
            primary_image = variant.images.first()
            
        data = {
            'id': variant.id,
            'product_id': variant.product.id,
            'product_name': variant.product.name,
            'color': variant.color,
            'price': variant.price,
            'discount_price': variant.discount_price,
            'image_url': primary_image.image.url if primary_image else None,
            'stock': sum(size.stock for size in variant.sizes.all()),
            'sizes': [{'id': size.id, 'size': size.size, 'stock': size.stock} for size in variant.sizes.all()]
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

