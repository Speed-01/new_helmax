from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate,logout as auth_logout
from django.contrib import messages
from django.utils.timezone import now
from manager.forms import SignupForm, OTPVerificationForm, PasswordResetRequestForm,SetPasswordForm
from .forms import AddressForm
from manager.models import OTP,User,Category, Brand, Size, Product, Variant, ProductImage, Review, Address, Cart, CartItem,PaymentMethod, Coupon, CouponUsage, Wishlist
from datetime import timezone
from django.views.decorators.cache import never_cache
from django.http import  JsonResponse
import json
from django.conf import settings
from django.apps import apps
from .utils import send_otp_email
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
import logging  
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Prefetch
from django.urls import reverse   
from django.db.models import Q

import re
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render, redirect
from django.contrib import messages
import logging

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

@require_POST
def filter_products(request):
    data = json.loads(request.body)
    
    # Start with base queryset
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True,
        brand__is_active=True,
        variants__is_active=True
    ).distinct()
    
    # Apply category filters
    if data.get('categories'):
        products = products.filter(category_id__in=data['categories'])
    
    # Apply brand filters
    if data.get('brands'):
        products = products.filter(brand_id__in=data['brands'])
    
    # Apply price filter
    min_price = float(data.get('minPrice', 0))
    max_price = float(data.get('maxPrice', float('inf')))
    products = products.filter(
        variants__price__gte=min_price,
        variants__price__lte=max_price
    ).distinct()
    
    # Apply search
    if data.get('search'):
        search_query = data['search']
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    sort_by = data.get('sort', 'new_arrivals')
    if sort_by == 'price_low_high':
        products = products.order_by('variants__price')
    elif sort_by == 'price_high_low':
        products = products.order_by('-variants__price')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    else:  # new_arrivals
        products = products.order_by('-id')
    
    # Prepare product data
    product_data = prepare_product_data(products)
    
    # Pagination
    page = int(data.get('page', 1))
    paginator = Paginator(product_data, 12)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'products': list(page_obj),
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages
    })

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
    print("signup_data",signup_data)
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
                    print("signup_data['email']",signup_data['email'])
                    # username = signup_data['email'].split('@')[0]
                    user = User.objects.create_user(
                        username=signup_data['first_name'],
                        email=signup_data['email'],
                        phone=signup_data['phone'],
                        password=signup_data['password1'],
                        first_name=signup_data.get('first_name', ''),
                        last_name=signup_data.get('last_name', ''),
                    )
                    print("user is created")
                    print("the user.......",user)
                    
                    request.session.pop('signup_data', None)
                    otp_instance.delete()

                    messages.success(request, 'Account created successfully! Please log in.')
                    return redirect('home')

                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
                    return redirect('signup')

            except OTP.DoesNotExist:
                messages.error(request, 'Invalid session. Please try again.')
                return redirect('signup')
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
        time_remaining = 0

    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': time_remaining})



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
            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
    
    except OTP.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Unable to process your request. Please try signing up again.'})






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
    
    return redirect('/')

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
        brand__is_active=True,
        variants__is_active=True  # Only products with active variants
    ).select_related(
        'category', 
        'brand'
    ).prefetch_related(
        'variants',
        'variants__images',
        'variants__sizes'
    ).distinct().order_by('-id')

    # Prepare product data for template
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

            # Calculate discount percentage if applicable
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

    # Pagination
    paginator = Paginator(product_data, 12)  # 12 products per page
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)
    
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
    if primary_variant:
        sizes = primary_variant.sizes.all().values('name', 'stock')
    
    context = {
        'product': product,
        'brand': product.brand.name,
        'primary_variant': primary_variant,
        'variants_with_images': variants_with_images,
        'sizes': sizes,
    }
    
    return render(request, 'product_details.html', context)
######### CART ########

from django.contrib.auth.decorators import login_required
from django.db import transaction


# In your app's views.py file
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from manager.models import Variant, CartItem, Cart


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

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import logging

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

        return render(request, 'wishlist.html', {
            'wishlist_items': items_data
        })
        
    except Exception as e:
        messages.error(request, "Error loading wishlist")
        return redirect('home')

@login_required
def move_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        is_added = False
    else:
        wishlist.products.add(product)
        is_added = True
    
    return JsonResponse({
        'is_added': is_added,
        'wishlist_count': wishlist.count
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
def remove_from_wishlist(request, item_id):
    """Remove item from wishlist"""
    try:
        wishlist_item = Wishlist.objects.get(id=item_id, user=request.user)
        wishlist_item.delete()
        return JsonResponse({'success': True})
    except Wishlist.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found'})

# Optional: Add to wishlist directly from products
@login_required
@require_POST
def add_to_wishlist(request, variant_id):
    """Add item directly to wishlist"""
    variant = get_object_or_404(Variant, id=variant_id)
    Wishlist.objects.get_or_create(user=request.user, variant=variant)
    return JsonResponse({'success': True, 'message': 'Added to wishlist!'})



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



# @csrf_exempt
# def edit_user_profile(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             full_name = data.get('full_name')
#             phone = data.get('phone')

#             # Assume the user is authenticated; get the current user
#             user = request.user
#             user.first_name = full_name
#             user.profile.phone = phone  # If phone is stored in a profile model
#             user.save()

#             return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
#         except Exception as e:
#             return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
#     return JsonResponse({'success': False, 'message': 'Invalid request method'})




################## Addresss ####################


@never_cache
@login_required(login_url='userlogin')
def userManageAddress(request):
    user_addresses = Address.objects.filter(user=request.user, is_deleted=False)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # Handle default address setting
            if address.is_default:
                with transaction.atomic():
                    Address.objects.filter(user=request.user).update(is_default=False)
            
            address.save()
            return JsonResponse({'success': True, 'message': 'Address added successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Error in adding address', 'errors': form.errors})

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
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)



################ checout #####################

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
import logging

from manager.models import Cart, CartItem, Address, PaymentMethod, Order, OrderItem




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
        }

        return render(request, 'checkout.html', context)

    except Exception as e:
        logger.error(f"Checkout error for user {request.user.id}: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('view_cart')
    
    
logger = logging.getLogger(__name__)

@login_required(login_url='userlogin')
@require_POST
@transaction.atomic
def place_order(request):
    try:
        # Get address and payment method from POST data
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')

        # Validate address exists and belongs to user
        try:
            selected_address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid address'}, status=400)

        # Get user's cart
        cart = Cart.objects.filter(
            user=request.user, 
            is_ordered=False
        ).prefetch_related(
            'items', 
            'items__variant', 
            'items__size'
        ).first()

        if not cart or not cart.items.exists():
            return JsonResponse({'success': False, 'message': 'Your cart is empty.'}, status=400)

        # Final validation before creating order
        invalid_items = []
        valid_items = []

        for cart_item in cart.items.all():
            # Check if product/variant/category/brand is active
            if not cart_item.is_active:  # Uses CartItem's is_active property
                invalid_items.append(cart_item)
                continue

            # Check stock availability
            if cart_item.quantity > cart_item.size.stock:
                invalid_items.append(cart_item)
                continue

            valid_items.append(cart_item)

        # Remove invalid items from the cart
        for item in invalid_items:
            item.delete()

        if invalid_items:
            return JsonResponse({
                'success': False,
                'message': 'Some items are no longer available. Please review your cart.',
                'errors': [f"{item.variant.product.name} is unavailable" for item in invalid_items]
            }, status=400)

        if not valid_items:
            return JsonResponse({'success': False, 'message': 'No valid items in cart'}, status=400)

        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.total_price,
            paymentmethod_id=payment_method,
            payment_status='PENDING',
            order_status='PROCESSING',
            # Populate address fields
            full_name=selected_address.full_name,
            email=selected_address.email,
            phone=selected_address.phone,
            address_line1=selected_address.address_line1,
            address_line2=selected_address.address_line2,
            city=selected_address.city,
            state=selected_address.state,
            pincode=selected_address.pincode
        )

        # Create order items
        for cart_item in valid_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.variant.product,
                variant=cart_item.variant,
                size=cart_item.size,
                quantity=cart_item.quantity,
                price=cart_item.variant.discount_price or cart_item.variant.price,
                status='Processing'
            )

            # Update stock
            cart_item.size.stock = F('stock') - cart_item.quantity
            cart_item.size.save()

        # Refresh size objects
        for cart_item in valid_items:
            cart_item.size.refresh_from_db()
            if cart_item.size.stock < 0:
                raise ValidationError(
                    f"Insufficient stock for {cart_item.variant.product.name}"
                )

        # Update cart
        cart.is_ordered = True
        cart.is_active = False
        cart.save()

        return JsonResponse({
            'success': True,
            'redirect_url': reverse('order_confirmation', args=[order.id])
        })

    except Exception as e:
        logger.error(f"Error in place_order: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e),
            'error_type': 'system'
        }, status=500)





from django.db.models import F


################# Order ####################
from manager.models import Order, OrderItem, Cart, CartItem
 

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
        .select_related('paymentmethod')\
        .order_by('-created_at')
        
    logger.debug(f"Fetched {orders.count()} orders for user {request.user.id}")
    
    for order in orders:
        logger.debug(f"Order {order.id} status: {order.order_status}")
    
    context = {'orders': orders}
    return render(request, 'my_orders.html', context)

@login_required(login_url='userlogin')
def order_confirmation(request, order_id):
    try:
        order = get_object_or_404(
            Order.objects.prefetch_related(
                'order_items',
                'order_items__product',
                'order_items__variant',
                'order_items__size'  
            ),
            id=order_id,
            user=request.user
        )
        order_items = order.order_items.all()
        logger.debug(f"Fetched order confirmation for order {order_id}")
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found in confirmation page")
        messages.error(request, "Order Not found.")
        return redirect('my_orders')
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'order_confirmation.html', context)

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
            if order.order_status not in ['PENDING', 'PROCESSING']:
                logger.warning(f"Cannot cancel order {order_id} with status {order.order_status}")
                return JsonResponse({
                    'success': False, 
                    'message': f'Cannot cancel order with status {order.order_status}'
                })
            
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
                except Exception as e:
                    logger.error(
                        f"Error restoring stock for order item {order_item.id}: {str(e)}"
                    )
                    raise  # Re-raise the exception to trigger rollback
            
            # Update order status
            order.order_status = 'CANCELLED'
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
    
    return render(request, 'store/available_coupons.html', {
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
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'})