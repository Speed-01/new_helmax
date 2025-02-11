from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate,logout as auth_logout
from django.contrib import messages
from django.utils.timezone import now
from manager.forms import SignupForm, OTPVerificationForm, PasswordResetRequestForm,SetPasswordForm
from .forms import AddressForm
from manager.models import OTP,User,Category, Brand, Size, Product, Variant, ProductImage, Review, Address, Cart, CartItem, Wishlist,PaymentMethod
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'login.html')

    if request.user.is_authenticated:
        return redirect('home')
    
    return render(request, 'login.html')

from django.urls import reverse   






# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created:
#         User.objects.create(user=instance)
#     else:
#         instance.User.save()



# @csrf_exempt  # For simplicity; use CSRF token in production
# def auth_receiver(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

#     try:
#         # Parse JSON data from request body
#         data = json.loads(request.body)
#         credential = data.get('credential')

#         if not credential:
#             return JsonResponse({'error': 'No credential provided'}, status=400)

#         # Verify token with Google
#         CLIENT_ID = settings.GOOGLE_OAUTH_CLIENT_ID
#         try:
#             id_info = id_token.verify_oauth2_token(
#                 credential,
#                 requests.Request(),
#                 CLIENT_ID
#             )

#             # Extract user info
#             email = id_info.get('email')
#             first_name = id_info.get('given_name', '')
#             last_name = id_info.get('family_name', '')

#             # Retrieve or create user
#             user, created = User.objects.get_or_create(
#                 email=email,
#                 defaults={'username': email.split('@')[0], 'first_name': first_name, 'last_name': last_name}
#             )

#             # Log the user in
#             auth_login(request, user)
#             return JsonResponse({'success': True, 'redirect_url': '/store/home/'})

#         except ValueError as e:
#             print(f"Token verification error: {str(e)}")
#             return JsonResponse({'error': 'Invalid token', 'details': str(e)}, status=400)

#     except Exception as e:
#         import traceback
#         print(f"Error in auth_receiver: {traceback.format_exc()}")
#         return JsonResponse({'error': 'Authentication failed'}, status=400)



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "No account found with this email.")
                return render(request, 'forgot_password.html')
            
            otp_instance, created = OTP.objects.get_or_create(email=email)
            otp_instance.generate_otp()
            print(otp_instance.otp)
            
            try:
                send_otp_email(email, otp_instance.otp, purpose="reset")
                request.session['reset_email'] = email
                messages.success(request, "OTP sent to your email.")
                return redirect('reset_password')
            except Exception as e:
                messages.error(request, "Failed to send OTP email. Please try again.")
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            
    return render(request, 'forgot_password.html')

def reset_password(request):
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, "Please submit your email first.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        otp = request.POST.get('otp')
        
        try:
            otp_instance = OTP.objects.get(email=reset_email)
            if otp_instance.is_valid() and otp_instance.otp == otp:
                if form.is_valid():
                    user = User.objects.get(email=reset_email)
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    del request.session['reset_email']
                    messages.success(request, "Password has been reset successfully!")
                    return redirect('login')
            else:
                messages.error(request, "Invalid or expired OTP.")
        except (OTP.DoesNotExist, User.DoesNotExist):
            messages.error(request, "Invalid reset attempt.")
    else:
        form = SetPasswordForm()
    
    return render(request, 'reset_password.html', {'form': form})


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
    
    # Calculate total stock by summing all size stocks
    total_stock = sum(size.stock for size in variant.sizes.all())
    
    # Get primary image
    primary_image = variant.images.filter(is_primary=True).first()
    
    data = {
        'id': variant.id,
        'color': variant.color,
        'price': str(variant.price),  # Convert Decimal to string for JSON
        'discount_price': str(variant.discount_price) if variant.discount_price else None,
        'total_stock': total_stock,  # Only using total from sizes
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
        'primary_image_url': primary_image.image.url if primary_image else (
            variant.images.first().image.url if variant.images.exists() else None
        )
    }
    
    return JsonResponse(data)




def product_list(request):
    # Start with base queryset of active products
    products = (
        Product.objects.filter(
            is_active=True,
            category__is_active=True,
            brand__is_active=True,
        )
        .select_related('category', 'brand')
        .prefetch_related(
            Prefetch(
                'variants',
                queryset=Variant.objects.filter(is_active=True).prefetch_related(
                    Prefetch(
                        'images',
                        queryset=ProductImage.objects.filter(is_primary=True),
                        to_attr='primary_images'
                    ),
                    'sizes'  # Prefetch sizes for stock calculation
                ),
                to_attr='active_variants'
            )
        )
    )

    # Sorting Logic
    sort_by = request.GET.get('sort', '')
    if sort_by == 'price_low_high':
        products = products.annotate(
            variant_price=Subquery(
                Variant.objects.filter(
                    product=OuterRef('pk'),
                    is_active=True
                ).order_by('price').values('price')[:1]
            )
        ).order_by('variant_price')
    elif sort_by == 'price_high_low':
        products = products.annotate(
            variant_price=Subquery(
                Variant.objects.filter(
                    product=OuterRef('pk'),
                    is_active=True
                ).order_by('-price').values('price')[:1]
            )
        ).order_by('-variant_price')
    elif sort_by == 'new_arrivals':
        products = products.order_by('-id')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')

    # Prepare product data for template
    product_data = []
    for product in products:
        if hasattr(product, 'active_variants') and product.active_variants:
            first_variant = product.active_variants[0]
            primary_image = first_variant.primary_images[0] if first_variant.primary_images else None
            
            # Calculate total stock for all variants
            total_stock = 0
            variant_stock_info = []
            
            for variant in product.active_variants:
                # Calculate variant's total stock (sum of sizes' stock)
                total_stock = sum(size.stock for size in variant.sizes.all())
                
                
                # # Prepare variant stock info
                # variant_stock_info.append({
                #     'color': variant.color or 'Default',
                #     'base_stock': variant.stock,
                #     'sizes': [
                #         {
                #             'size': size.get_name_display(),  # This will show the human-readable size name
                #             'stock': size.stock
                #         } for size in variant.sizes.all()
                #     ],
                #     'total_stock': variant_total_stock
                # })
            
            product_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': first_variant.discount_price or first_variant.price,
                'image_url': primary_image.image.url if primary_image else 'default_image.jpg',
                'total_stock': total_stock,
                'stock_status': 'In Stock' if total_stock > 0 else 'Out of Stock'
            })

    # Pagination Logic
    paginator = Paginator(product_data, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': Category.objects.filter(is_active=True),
        'brands': Brand.objects.filter(is_active=True),
        'sort_by': sort_by,
    }

    return render(request, 'product_list.html', context)
def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand')
        .prefetch_related(
            'variants',
            'variants__sizes',
            'variants__images'
        ),
        id=product_id,
        is_active=True
    )
    
    variants = list(product.variants.filter(is_active=True))
    primary_variant = variants[0] if variants else None
    
    variants_with_images = []
    for variant in variants:
        primary_image = variant.images.filter(is_primary=True).first()
        variants_with_images.append({
            'variant': variant,
            'primary_image': primary_image,
            'id': variant.id,
            'color': variant.color,
            'stock': variant.get_total_stock(),
            'in_stock': variant.is_in_stock()
        })
    
    # Get sizes with stock information for primary variant
    if primary_variant:
        sizes = [
            {
                'name': size.name,
                'stock': size.stock,
                'display_name': size.get_name_display(),
                'available': size.stock > 0
            }
            for size in primary_variant.sizes.all()
        ]
        total_stock = sum(size['stock'] for size in sizes)
    else:
        sizes = []
        total_stock = 0

    context = {
        'product': product,
        'brand': product.brand.name, 
        'primary_variant': primary_variant,
        'variants_with_images': variants_with_images,  
        'stock_status': 'In Stock' if total_stock > 0 else 'Out of Stock',
        'sizes': sizes,
        'total_stock': total_stock
    }
    
    return render(request, 'product_details.html', context)
######### CART ########

from django.contrib.auth.decorators import login_required
from django.db import transaction
from manager.models import Cart, CartItem, Variant, Size, Wishlist

# In your app's views.py file
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from manager.models import Variant, CartItem, Cart


@login_required

def view_cart(request):
    if not request.user.is_authenticated:
        
        return redirect('Login')  

   
    cart, created = Cart.objects.get_or_create(
        user=request.user,
        is_ordered=False,
        defaults={'is_active': True}
    )

   
    cart_items = cart.items.select_related('variant', 'size').all()

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

        # Check size stock instead of variant stock
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
def move_to_wishlist(request, item_id):
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            
            # Check if the item is already in the wishlist
            if Wishlist.objects.filter(user=request.user, variant=cart_item.variant).exists():
                return JsonResponse({'success': False, 'message': 'Item is already in your wishlist.'})
            
            # Add to wishlist
            Wishlist.objects.get_or_create(
                user=request.user,
                variant=cart_item.variant
            )
            
            # Remove from cart
            cart_item.delete()
            
            return JsonResponse({'success': True, 'message': 'Item moved to wishlist successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
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

# Configure logging
logger = logging.getLogger(__name__)

@login_required(login_url='userlogin')
@never_cache
def user_checkout(request):
    try:
        # Check if cart exists and has items
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

        # Fetch user addresses and payment methods
        user_addresses = Address.objects.filter(user=request.user, is_deleted=False)
        if not user_addresses.exists():
            messages.warning(request, "Please add a delivery address to proceed")
            return redirect('userManageAddress')

        payment_methods = PaymentMethod.objects.all()

        # Validate cart items and check stock
        total_quantity = 0
        cart_items = []
        stock_warnings = []

        for item in cart.items.all():
            if not item.variant or not item.size:
                messages.warning(
                    request,
                    f"One of your cart items is invalid and has been removed."
                )
                item.delete()
                continue

            # Check stock availability
            if item.quantity > item.size.stock:
                if item.size.stock == 0:
                    stock_warnings.append(
                        f"{item.variant.product.name} - {item.size.get_name_display()} is out of stock"
                    )
                else:
                    stock_warnings.append(
                        f"Only {item.size.stock} units available for {item.variant.product.name} - {item.size.get_name_display()}"
                    )
                continue

            total_quantity += item.quantity
            cart_items.append(item)

        # If there are stock warnings, show them and redirect
        if stock_warnings:
            for warning in stock_warnings:
                messages.warning(request, warning)
            return redirect('view_cart')

        # If cart is empty after validation, redirect
        if not cart_items:
            messages.warning(request, "No valid items in cart")
            return redirect('view_cart')

        # Check minimum order amount if applicable
        min_order_amount = 0  # Set your minimum amount
        if cart.total_price < min_order_amount:
            messages.warning(
                request, 
                f"Minimum order amount is ₹{min_order_amount}"
            )
            return redirect('view_cart')

        context = {
            'user_addresses': user_addresses,
            'cart_items': cart_items,
            'cart': cart,
            'total_price': cart.total_price,
            'total_discount': cart.total_discount,
            'final_price': cart.final_price,
            'payment_methods': payment_methods,
            'total_quantity': total_quantity,
        }

        return render(request, 'checkout.html', context)

    except Exception as e:
        logger.error(
            f"Checkout error for user {request.user.id}: {str(e)}", 
            exc_info=True
        )
        messages.error(
            request, 
            "An unexpected error occurred. Please try again."
        )
        return redirect('view_cart')






from django.db.models import F


################# Order ####################
from manager.models import Order, OrderItem, Cart, CartItem
 
@login_required(login_url='userlogin')
def my_orders(request):
    orders = Order.objects.filter(user=request.user)\
        .prefetch_related(
            'order_items',
            'order_items__product',
            'order_items__variant',
            'order_items__variant__images'
        )\
        .select_related('paymentmethod')\
        .order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'my_orders.html', context)


@login_required(login_url='userlogin')
@transaction.atomic
def place_order(request):
    logger.debug("Starting place_order view")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"POST data: {request.POST}")

    if request.method == 'POST':
        try:
            address_id = request.POST.get('address_id')
            payment_method = request.POST.get('payment_method')
            
            logger.debug(f"Address ID: {address_id}")
            logger.debug(f"Payment Method: {payment_method}")

            # Validate address exists and belongs to user
            try:
                selected_address = Address.objects.get(id=address_id, user=request.user)
                logger.debug(f"Found address: {selected_address}")
            except Address.DoesNotExist as e:
                logger.error(f"Address validation failed: {str(e)}")
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

            logger.debug(f"Found cart: {cart}")
            
            if not cart or not cart.items.exists():
                logger.error("Cart is empty or not found")
                return JsonResponse({'success': False, 'message': 'Your cart is empty.'}, status=400)

            # Stock validation
            stock_errors = []
            for cart_item in cart.items.all():
                logger.debug(f"Checking stock for item: {cart_item.variant.product.name}")
                
                if not cart_item.size:
                    stock_errors.append(f"Size not selected for {cart_item.variant.product.name}")
                    continue
                
                if cart_item.size.stock < cart_item.quantity:
                    if cart_item.size.stock == 0:
                        stock_errors.append(
                            f"{cart_item.variant.product.name} - {cart_item.size.get_name_display()} is out of stock"
                        )
                    else:
                        stock_errors.append(
                            f"Only {cart_item.size.stock} units available for {cart_item.variant.product.name}"
                        )

            if stock_errors:
                logger.error(f"Stock validation failed: {stock_errors}")
                return JsonResponse({
                    'success': False, 
                    'message': 'Stock validation failed',
                    'errors': stock_errors
                }, status=400)

            try:
                # Create order
                logger.debug("Creating order")
                order = Order.objects.create(
                    user=request.user,
                    total_amount=cart.total_price,
                    paymentmethod_id=payment_method,
                    payment_status='PENDING',
                    order_status='PROCESSING',
                    # Address fields
                    full_name=selected_address.full_name,
                    email=selected_address.email,
                    phone=selected_address.phone,
                    address_line1=selected_address.address_line1,
                    address_line2=selected_address.address_line2,
                    city=selected_address.city,
                    state=selected_address.state,
                    pincode=selected_address.pincode
                )
                logger.debug(f"Order created: {order.id}")

                # Create order items
                for cart_item in cart.items.all():
                    logger.debug(f"Creating order item for: {cart_item.variant.product.name}")
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
                    logger.debug(f"Updated stock for size: {cart_item.size}")

                # Refresh size objects
                for cart_item in cart.items.all():
                    cart_item.size.refresh_from_db()
                    if cart_item.size.stock < 0:
                        raise ValidationError(
                            f"Insufficient stock for {cart_item.variant.product.name}"
                        )

                # Update cart
                cart.is_ordered = True
                cart.is_active = False
                cart.save()
                logger.debug("Cart marked as ordered")

                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('order_confirmation', args=[order.id])
                })

            except Exception as e:
                logger.error(f"Error creating order: {str(e)}", exc_info=True)
                raise  # Re-raise to be caught by outer try-catch

        except Exception as e:
            logger.error(f"Error in place_order: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e),
                'error_type': 'system'
            }, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)


@login_required(login_url='userlogin')
def order_confirmation(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order_items = order.order_items.all()
        
        print("order items >>>>>>>",order_items)
    except Order.DoesNotExist:
        messages.error(request, "Order Not found.")
        return redirect('my_orders')
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'order_confirmation.html', context)
# views.py
from django.http import JsonResponse

@login_required
def cancel_order(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            # Update the order status to CANCELLED
            order.order_status = 'CANCELLED'
            order.save()
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})