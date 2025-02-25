from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from PIL import Image
from django.core.paginator import Paginator
from .models import Product,Category,ProductImage,User, Brand, Variant, Size, Coupon, CouponUsage, Order, ReturnRequest, Wallet, WalletTransaction
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
import json



def search_products(request):
    query = request.GET.get('q', '').strip()
    products = []

    if query:
        # Filter products by name or description
        products = Product.objects.filter(name__icontains=query).values('id', 'name', 'description')

    return JsonResponse({'products': list(products)})



@never_cache
def adminLogin(request):
    if request.user.is_authenticated:
        return redirect("customers")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect("adminLogin")
        elif user and user.is_superuser:
            login(request, user)
            return redirect("customers")
        else:
            messages.error(request, f"{user} have no access to this page")
            return redirect("adminLogin")
    return render(request, "adminLogin.html")

@never_cache

def admin_logout(request):
    logout(request)
    return redirect('adminLogin')










def customers(request):
    credential = request.GET.get("value", "")
    if credential:
        customers = User.objects.filter(
            Q(username__icontains=credential) | Q(email__icontains=credential)
        ).exclude(is_superuser=True)
    else:
        customers = User.objects.all().exclude(is_superuser=True)
        
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(first_name__icontains=search_query)

    paginator = Paginator(customers, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "customers": page_obj,
        "search_query": search_query
    }

    return render(request, "customers.html", context)



@login_required
def toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if not user.is_superuser:  
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({
                'success': True,
                'status': 'active' if user.is_active else 'blocked'
            })
        
    return JsonResponse({'success': False}, status=400)
        



from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse

def admin_category(request):
    search_query = request.GET.get('search', '')
    
    # Filter categories based on search query
    categories = Category.objects.all().order_by("-id")
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(categories, 10)  # 10 items per page
    page_obj = paginator.get_page(page_number)
    
    context ={
        'categories': page_obj,
        'search_query': search_query
    }
    
    return render(request, 'admincategory.html', context )


def add_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        if name:  
            if Category.objects.filter(name__iexact=name).exists():
                
                error_message = "Category with this name already exists."
                return render(request, 'admincategory.html', {
                    'categories': Category.objects.all(),
                    'error_message': error_message,
                    'show_add_modal': True,  
                })
            else:
                Category.objects.create(name=name)
                print("Category added successfully")
        return redirect('admin_category')  
    return redirect('admin_category')



def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        name = request.POST.get('category_name')
        if name:
            if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                error_message = "Category with this name already exists."
                return render(request, 'admincategory.html', {
                    'categories': Category.objects.all(),
                    'error_message': error_message,
                    'edit_category': category,
                    'show_edit_modal': True,
                })
            else:
                category.name = name
                category.save()
                print("Category updated successfully")
        return redirect('admin_category')
    return render(request, 'edit_category.html', {'category': category})




def toggle_category_status(request, category_id):
    print(f"Toggling category {category_id}")
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.is_active = not category.is_active
        category.save()
        print(f"New status: {'active' if category.is_active else 'blocked'}")
        return JsonResponse({
            'success': True,
            'status': 'active' if category.is_active else 'blocked'
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


# def delete_category(request, category_id):
#     category = get_object_or_404(Category, id=category_id)
#     category.is_deleted = True
#     category.save()
#     print("Category deleted successfully")
#     return redirect('admin_category')



def admin_brand(request):
    # Fetch all brands ordered by ID in descending order
    brands = Brand.objects.all().order_by("-id")
    
    # Search functionality for brands
    search_query = request.GET.get('search', '')
    if search_query:
        
        brands = brands.filter(name__icontains=search_query)
    
    # Paginate brands
    paginator = Paginator(brands, 10)  # Show 10 brands per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare context
    context = {
        'brands': page_obj,  # Pass the paginated brands
        'search_query': search_query,  # Pass the search query
    }
    
    # Render the template with the context
    return render(request, 'adminBrand.html', context)

def add_brand(request):
    if request.method == "POST":
        name = request.POST.get('brand_name')
        if name and not Brand.objects.filter(name__iexact=name).exists():
            Brand.objects.create(name=name)
        return redirect('admin_brand')
    return redirect('admin_brand')

def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == "POST":
        
        name = request.POST.get('brand_name')
        if name and not Brand.objects.filter(name__iexact=name).exclude(id=brand_id).exists():
            brand.name = name
            brand.save()
        return redirect('admin_brand')
    return render(request, 'editBrand.html', {'brand': brand})

def toggle_brand_status(request, brand_id):
    if request.method == 'POST':
        brand = get_object_or_404(Brand, id=brand_id)
        brand.is_active = not brand.is_active
        brand.save()
        return JsonResponse({
            'success': True,
            'status': 'active' if brand.is_active else 'blocked'
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)








def adminProducts(request):
    # Fetch all products ordered by ID
    products = Product.objects.all().order_by('id')
    
    # Pagination Logic
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')  # Get the current page number from the request
    page_obj = paginator.get_page(page_number)  # Get the page object

    context = {
        'page_obj': page_obj,  # Pass the paginated page object to the template
    }
    return render(request, 'adminProducts.html', context)


from django.db.models import Q

def addProducts(request):
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Get and sanitize input
        name = request.POST.get('name', '').strip()  # Remove leading/trailing whitespace
        brand_id = request.POST.get('brand')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '').strip()

        # Validate all fields are not empty
        if not name or not brand_id or not category_id or not description:
            messages.error(request, "All fields are required.")
            return render(request, 'addProducts.html', {'categories': categories, 'brands': brands})

        # # Validate product name (no symbols or only spaces)
        # if not name.replace(" ", "").isalnum():
        #     messages.error(request, "Product name cannot contain only symbols or spaces.")
        #     return render(request, 'addProducts.html', {'categories': categories, 'brands': brands})

        # Case-insensitive uniqueness check
        if Product.objects.filter(name__iexact=name).exists():
            messages.error(request, f"A product with the name '{name}' already exists (case-insensitive).")
            return render(request, 'addProducts.html', {'categories': categories, 'brands': brands})

        # Create product if valid
        try:
            category = get_object_or_404(Category, id=category_id)
            brand = get_object_or_404(Brand, id=brand_id)
            
            Product.objects.create(
                name=name,
                brand=brand,
                category=category,
                description=description
            )
            messages.success(request, "Product added successfully!")
            return redirect('adminProducts')
            
        except Exception as e:
            messages.error(request, f"Error creating product: {str(e)}")

    return render(request, 'addProducts.html', {'categories': categories, 'brands': brands})

def addVariant(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        color = request.POST.get('color')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        sizes = request.POST.getlist('sizes')
        images = request.FILES.getlist('images')
        primary_image_index = int(request.POST.get('primary_image_index', 0))  # New field

        try:
            with transaction.atomic():  # Use transaction to ensure data consistency
                # Create variant
                variant = Variant.objects.create(
                    product=product,
                    color=color,
                    price=price,
                    discount_price=discount_price if discount_price else None
                )

                # Create sizes with their respective stocks
                for size in sizes:
                    stock_for_size = request.POST.get(f'stock_{size}', 0)
                    stock_value = int(stock_for_size) if stock_for_size else 0
                    
                    Size.objects.create(
                        product_variant=variant,
                        name=size,
                        stock=stock_value
                    )

                # Handle images
                for index, image in enumerate(images):
                    ProductImage.objects.create(
                        variant=variant,
                        image=image,
                        is_primary=(index == primary_image_index)  # Set primary based on selected index
                    )

            messages.success(request, 'Variant added successfully.')
        except Exception as e:
            messages.error(request, f'Error adding variant: {str(e)}')

        return redirect('adminProducts')

    context = {
        'product': product,
        'size_choices': Size.SIZE_CHIOCES
    }
    return render(request, 'addVariant.html', context)

def editProduct(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            brand_id = request.POST.get('brand')
            category_id = request.POST.get('category')
            description = request.POST.get('description')

            product.name = name
            product.brand = get_object_or_404(Brand, id=brand_id)
            product.category = get_object_or_404(Category, id=category_id)
            product.description = description
            product.save()

            return redirect('adminProducts')
        except Exception as e:
            print(f"Error: {e}")
    
    context = {
        'product': product,
        'categories': categories,
        'brands': brands
    }
    return render(request, 'editProduct.html', context)

def editVariant(request, variant_id):
    variant = get_object_or_404(Variant, id=variant_id)
    product = variant.product
    existing_sizes = variant.sizes.all()
    existing_images = variant.images.all()
    
    if request.method == 'POST':
        color = request.POST.get('color')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        new_sizes = request.POST.getlist('sizes')
        new_images = request.FILES.getlist('images')
        
        try:
            # Update variant details
            variant.color = color
            variant.price = price
            variant.discount_price = discount_price
            variant.stock = 0  # Will be updated based on size stocks
            variant.save()
            
            existing_sizes = {size.name: size for size in variant.sizes.all()}
            total_stock = 0

            for size_code in new_sizes:
                stock_key = f'stock_{size_code}'
                stock_value = int(request.POST.get(stock_key, 0))
                
                if size_code in existing_sizes:
                    # Update existing size
                    size_obj = existing_sizes[size_code]
                    size_obj.stock = stock_value
                    size_obj.save()
                    del existing_sizes[size_code]
                else:
                    # Create new size
                    Size.objects.create(
                        product_variant=variant,
                        name=size_code,
                        stock=stock_value
                    )
                
                total_stock += stock_value

            # Handle sizes not in new_sizes
            for size_name, size_obj in existing_sizes.items():
                if size_obj.cartitem_set.exists():
                    # Set stock to 0 to retain cart items
                    size_obj.stock = 0
                    size_obj.save()
                else:
                    size_obj.delete()

            variant.stock = total_stock
            variant.save()
            
            # Handle new images
            if new_images:
                if len(new_images) < 4:
                    messages.error(request, 'Please upload at least 4 images.')
                    return redirect('editVariant', variant_id=variant.id)
                    
                # If new images are uploaded, delete old ones
                existing_images.delete()
                
                # Add new images
                for index, image in enumerate(new_images):
                    ProductImage.objects.create(
                        variant=variant,
                        image=image,
                        is_primary=(index == 0)
                    )
        
            messages.success(request, 'Variant updated successfully.')
            return redirect('adminProducts')
            
        except Exception as e:
            messages.error(request, f'Error updating variant: {str(e)}')
            return redirect('editVariant', variant_id=variant.id)
    
    # Prepare size data for template
    size_data = []
    for size_code, size_name in Size.SIZE_CHIOCES:
        existing_size = existing_sizes.filter(name=size_code).first()
        size_data.append({
            'code': size_code,
            'name': size_name,
            'checked': existing_size is not None,
            'stock': existing_size.stock if existing_size else 0
        })
    
    context = {
        'product': product,
        'variant': variant,
        'size_data': size_data,
        'existing_images': existing_images
    }
    return render(request, 'editVariant.html', context)

def deleteProduct(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        try:
            # Set is_active to False instead of actually deleting
            product.is_active = False
            product.save()
            messages.success(request, 'Product blocked successfully')
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')
        
    return redirect('adminProducts')

def deleteVariant(request, variant_id):
    if request.method == 'POST':
        variant = get_object_or_404(Variant, id=variant_id)
        try:
            # Set is_active to False instead of actually deleting
            variant.is_active = False
            variant.save()
            messages.success(request, 'Variant deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting variant: {str(e)}')
    
    return redirect('adminProducts')


def toggle_product_status(request, product_id):
    print(f"Toggling status for product ID: {product_id}")
    try:
        product = Product.objects.get(id=product_id)
        product.is_active = not product.is_active
        product.save()
        
       
        return JsonResponse({'success': True, 'status': 'active' if product.is_active else 'blocked'})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

def toggleVariant(request, variant_id):
    if request.method == 'POST':
        variant = get_object_or_404(Variant, id=variant_id)
        try:
            variant.is_active = not variant.is_active
            variant.save()
            status = "unblocked" if variant.is_active else "blocked"
            messages.success(request, f'Variant successfully {status}')
        except Exception as e:
            messages.error(request, f'Error updating variant status: {str(e)}')
    return redirect('adminProducts')


############## orders   ####################

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Order, ReturnRequest
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

from django.core.paginator import Paginator

# views.py
def admin_orders(request):
    # Handle initial page render (HTML)
    orders = Order.objects.select_related('user', 'paymentmethod').order_by('-created_at')
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(user__username__icontains=search_query)
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'orders': page_obj, 'search_query': search_query}
    return render(request, 'adminOrder.html', context)

from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Order

def admin_orders_api(request):
    try:
        # Fetch orders with related user, paymentmethod, and order items
        orders = Order.objects.select_related('user', 'paymentmethod').prefetch_related('order_items').order_by('-created_at')
        
        # Apply search filter
        search_query = request.GET.get('search', '')
        if search_query:
            orders = orders.filter(user__username__icontains=search_query)
        
        # Paginate results
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Prepare data for JSON response
        orders_data = []
        for order in page_obj:
            order_items = [
                {
                    'product_name': item.product.name if item.product else 'N/A',
                    'variant_details': f"{item.variant.color}" if item.variant else 'N/A',
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'status': item.status
                } for item in order.order_items.all()
            ]
            
            orders_data.append({
                'id': order.id,
                'username': order.user.username if order.user else 'N/A',
                'payment_method': order.paymentmethod.name if order.paymentmethod else 'N/A',
                'status': order.order_status,
                'total_price': float(order.total_amount) if order.total_amount else 0.0,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'items': order_items
            })
        
        return JsonResponse({
            'orders': orders_data,
            'total_pages': paginator.num_pages
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
import json
from .models import Order, OrderItem, ReturnRequest

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_detail.html', {'order': order})

@login_required
@require_POST
def update_order_status(request, order_id):
    try:
        data = json.loads(request.body)
        order = get_object_or_404(Order, id=order_id)
        
        # Enhanced check for cancelled orders
        if order.order_status == 'CANCELLED':
            return JsonResponse({
                'success': False, 
                'error': 'This order has been cancelled and cannot be modified'
            }, status=400)
            
        with transaction.atomic():
            order.order_status = data['status']
            order.save()
            order.order_items.all().update(status=data['status'].capitalize())
                
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        if order.order_status not in ['DELIVERED', 'CANCELLED']:
            with transaction.atomic():
                order.order_status = 'CANCELLED'
                order.save()
                order.order_items.all().update(status='Cancelled')
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Order cannot be cancelled'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})    

@login_required
@require_POST
def update_item_status(request):
    try:
        data = json.loads(request.body)
        item = get_object_or_404(OrderItem, id=data['item_id'])
        
        with transaction.atomic():
            item.status = data['status']
            if data['status'] in ['Cancelled', 'Returned'] and data.get('reason'):
                if data['status'] == 'Cancelled':
                    item.cancellation_reason = data['reason']
                else:
                    item.return_reason = data['reason']
            item.save()
            
            # Update order status if all items have the same status
            order = item.order
            all_items_status = set(order.order_items.values_list('status', flat=True))
            if len(all_items_status) == 1:
                order.order_status = data['status'].upper()
                order.save()
                
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# @login_required
# def handle_return_request(request, return_id):
#     try:
#         data = json.loads(request.body)
#         return_request = get_object_or_404(ReturnRequest, id=return_id)
        
#         with transaction.atomic():
#             return_request.status = data['action']
#             return_request.admin_response = data.get('response', '')
#             return_request.save()
            
#             # Update order and items status based on return request decision
#             order = return_request.order
#             new_status = 'RETURNED' if data['action'] == 'approved' else order.order_status
#             order.order_status = new_status
#             order.save()
            
#             if data['action'] == 'approved':
#                 order.order_items.all().update(status='Returned')
                
#         return JsonResponse({
#             'success': True,
#             'message': f'Return request has been {data["action"]}'
#         })
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})

def admin_coupons(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'admin_coupons.html', {'coupons': coupons})

def add_coupon(request):
    if request.method == 'POST':
        try:
            code = request.POST.get('code')
            coupon_type = request.POST.get('type')
            value = request.POST.get('value')
            minimum_purchase = request.POST.get('minimum_purchase')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            usage_limit = request.POST.get('usage_limit')
            is_active = request.POST.get('is_active') == 'on'

            # Validate coupon code uniqueness
            if Coupon.objects.filter(code=code).exists():
                messages.error(request, 'Coupon code already exists')
                return redirect('admin_coupons')

            # Create the coupon
            Coupon.objects.create(
                code=code,
                type=coupon_type,
                value=value,
                minimum_purchase=minimum_purchase,
                start_date=start_date,
                end_date=end_date,
                usage_limit=usage_limit,
                is_active=is_active
            )
            messages.success(request, 'Coupon added successfully')
            
        except Exception as e:
            messages.error(request, f'Error creating coupon: {str(e)}')
        
    return redirect('admin_coupons')

@require_POST
def delete_coupon(request, coupon_id):
    try:
        coupon = get_object_or_404(Coupon, id=coupon_id)
        coupon.delete()
        return JsonResponse({'success': True, 'message': 'Coupon deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Add this to your existing checkout view or create a new one
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        cart = request.user.cart_set.filter(is_ordered=False).first()
        
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
            usage_count = CouponUsage.objects.filter(
                coupon=coupon,
                user=request.user
            ).count()
            
            if usage_count >= coupon.usage_limit:
                return JsonResponse({
                    'success': False,
                    'message': 'Coupon usage limit exceeded'
                })
            
            # Calculate discount
            if coupon.type == 'percentage':
                discount = (cart.total_price * coupon.value) / 100
            else:
                discount = coupon.value
                
            return JsonResponse({
                'success': True,
                'discount': float(discount),
                'final_amount': float(cart.total_price - discount)
            })
            
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code'
            })

def get_coupon_details(request, coupon_id):
    try:
        coupon = get_object_or_404(Coupon, id=coupon_id)
        return JsonResponse({
            'code': coupon.code,
            'type': coupon.type,
            'value': str(coupon.value),
            'minimum_purchase': str(coupon.minimum_purchase),
            'start_date': coupon.start_date.strftime('%Y-%m-%d'),
            'end_date': coupon.end_date.strftime('%Y-%m-%d'),
            'usage_limit': coupon.usage_limit,
            'is_active': coupon.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def edit_coupon(request, coupon_id):
    if request.method == 'POST':
        try:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            
            # Check if code exists for other coupons
            if Coupon.objects.filter(code=request.POST.get('code')).exclude(id=coupon_id).exists():
                messages.error(request, 'Coupon code already exists')
                return redirect('admin_coupons')

            coupon.code = request.POST.get('code')
            coupon.type = request.POST.get('type')
            coupon.value = request.POST.get('value')
            coupon.minimum_purchase = request.POST.get('minimum_purchase')
            coupon.start_date = request.POST.get('start_date')
            coupon.end_date = request.POST.get('end_date')
            coupon.usage_limit = request.POST.get('usage_limit')
            coupon.is_active = request.POST.get('is_active') == 'on'
            coupon.save()
            
            messages.success(request, 'Coupon updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating coupon: {str(e)}')
    return redirect('admin_coupons')

@login_required
def admin_return_requests(request):
    return_requests = ReturnRequest.objects.select_related(
        'order_item', 'user'
    ).filter(status='PENDING')
    
    return render(request, 'admin_return_requests.html', {
        'return_requests': return_requests
    })

@login_required
@require_POST
def handle_return_request(request, request_id):
    try:
        data = json.loads(request.body)
        return_request = get_object_or_404(ReturnRequest, id=request_id)
        
        with transaction.atomic():
            return_request.status = data['action']
            return_request.admin_response = data.get('response', '')
            return_request.save()
            
            if data['action'] == 'APPROVED':
                order_item = return_request.order_item
                
                # Update item status
                order_item.status = 'Returned'
                order_item.save()
                
                # Restore stock
                order_item.size.stock += order_item.quantity
                order_item.size.save()
                
                # Add refund to wallet
                wallet, created = Wallet.objects.get_or_create(user=return_request.user)
                refund_amount = order_item.price * order_item.quantity
                
                wallet.balance += refund_amount
                wallet.save()
                
                # Record transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    transaction_type='REFUND',
                    description=f'Refund for returned item #{order_item.id}'
                )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})