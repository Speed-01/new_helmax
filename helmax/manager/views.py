from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from PIL import Image
from django.core.paginator import Paginator
from .models import Product,Category,ProductImage,User, Brand, Variant, Size
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST



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









@login_required
def customers(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active  
            user.save()
            messages.success(
                request, 
                f"User {user.username} has been {'activated' if user.is_active else 'blocked'}."
            )
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
        return redirect("customers")  

    credential = request.GET.get("value", "")
    if credential:
        customers = User.objects.filter(
            Q(username__icontains=credential) | Q(email__icontains=credential)
        ).exclude(is_superuser=True)
    else:
        customers = User.objects.all().exclude(is_superuser=True)

    context = {"customers": customers}
    return render(request, "customers.html", context)

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
        


def admin_category(request):
    
    categories = Category.objects.all().order_by("-id")
    return render(request, 'admincategory.html', {'categories': categories})

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
    brands = Brand.objects.all().order_by("-id")
    return render(request, 'adminBrand.html', {'brands': brands})

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
    # products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('variants__sizes', 'variants__images')
    products = Product.objects.all().order_by('id')
    paginator = Paginator(products, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'adminProducts.html', {'products': page_obj})

def addProducts(request):
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        brand = request.POST.get('brand')
        category = request.POST.get('category')
        description = request.POST.get('description')
        
        category = get_object_or_404(Category, id=category)
        brand = get_object_or_404(Brand, id=brand)
        
        product = Product.objects.create(
            name=name,
            brand=brand,
            description=description,
            category=category,
        )


        return redirect('adminProducts')

    return render(request, 'addProducts.html', {'categories': categories,'brands':brands})

def addVariant(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        color = request.POST.get('color')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        sizes = request.POST.getlist('sizes')
        images = request.FILES.getlist('images')

        try:
            # Create variant without stock first
            variant = Variant.objects.create(
                product=product,
                color=color,
                price=price,
                discount_price=discount_price,
                stock=0  # Will be updated based on size stocks
            )

            total_stock = 0
            # Create sizes with their respective stocks
            for size in sizes:
                stock_for_size = request.POST.get(f'stock_{size}', 0)
                stock_value = int(stock_for_size) if stock_for_size else 0
                total_stock += stock_value
                
                Size.objects.create(
                    product_variant=variant,
                    name=size,
                    stock=stock_value
                )
            
            # Update variant's total stock
            variant.stock = total_stock
            variant.save()

            # Handle images
            for index, image in enumerate(images):
                ProductImage.objects.create(
                    variant=variant,
                    image=image,
                    is_primary=(index == 0)
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
    all_sizes = ['S', 'M', 'L', 'XL']
    
    if request.method == 'POST':
        color = request.POST.get('color')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        discount_price = request.POST.get('discount_price')
        new_sizes = request.POST.getlist('sizes')
        new_images = request.FILES.getlist('images')
        
        # Update variant details
        variant.color = color
        variant.price = price
        variant.stock = stock
        variant.discount_price = discount_price
        variant.save()
        
        # Update sizes
        # Clear all existing sizes and add the new ones
        variant.sizes.all().delete()
        for size in new_sizes:
            Size.objects.create(product_variant=variant, name=size)
        
        # Handle new images
        if new_images:
            # If new images are uploaded, delete old ones
            existing_images.delete()
            
            # Add new images
            for index, image in enumerate(new_images):
                ProductImage.objects.create(
                    variant=variant,
                    image=image,
                    is_primary=(index == 0)
                )
        
        return redirect('adminProducts')
    
    context = {
        'product': product,
        'variant': variant,
        'all_sizes': all_sizes,
        'existing_sizes': [size.name for size in existing_sizes],
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

def admin_orders(request):
    orders = Order.objects.select_related('user').order_by('-created_at')
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(user__username__icontains=search_query)
    
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'orders': [
                {
                    'id': order.id,
                    'user__username': order.user.full_name,
                    'payment_method': order.payment_method,
                    'status': order.status,
                    'total_price': float(order.total_price)
                } for order in page_obj
            ],
            'total_pages': paginator.num_pages,
        }
        return JsonResponse(data)
    
    context = {
        'orders': page_obj,
        'search_query': search_query
    }
    return render(request, 'adminOrder.html', context)

def edit_order(request, order_id):
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items__product'), id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully')
            return redirect('admin_orders')
    
    context = {
        'order': order,
    }
    return render(request, 'editOrder.html', context)

def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status:
            order.status = new_status
            order.save()
            return JsonResponse({
                'success': True,
                'message': 'Order status updated successfully'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })

def handle_return_request(request, return_request_id):
    return_request = get_object_or_404(ReturnRequest, id=return_request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        response = request.POST.get('response', '')
        
        if action == 'approve':
            return_request.status = 'approved'
            return_request.order.status = 'returned'
            messages.success(request, 'Return request approved successfully')
        elif action == 'reject':
            return_request.status = 'rejected'
            messages.success(request, 'Return request rejected successfully')
            
        return_request.admin_response = response
        return_request.save()
        return_request.order.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

