from django.http import JsonResponse
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Order, OrderItem, Product, Category, Brand, User

# Configure logging
logger = logging.getLogger(__name__)

@login_required(login_url='adminLogin')
def get_dashboard_metrics(request):
    try:
        time_filter = request.GET.get('filter', 'monthly')
        now = timezone.now()
        
        # Set time range based on filter
        if time_filter == 'yearly':
            start_date = now - timedelta(days=365)
        elif time_filter == 'monthly':
            start_date = now - timedelta(days=30)
        else:  # weekly
            start_date = now - timedelta(days=7)
        
        # Calculate total revenue
        total_revenue = Order.objects.filter(
            created_at__gte=start_date,
            order_status='DELIVERED'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Calculate total orders
        total_orders = Order.objects.filter(
            created_at__gte=start_date
        ).count()
        
        # Calculate new customers
        new_customers = User.objects.filter(
            date_joined__gte=start_date
        ).count()
        
        return JsonResponse({
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'new_customers': new_customers
        })
    except Exception as e:
        logger.error(f'Error in get_dashboard_metrics: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch dashboard metrics', 'details': str(e)}, status=500)

@login_required(login_url='adminLogin')
def get_sales_data(request):
    try:
        filter_type = request.GET.get('filter', 'monthly')
        today = timezone.now()
        
        if filter_type == 'weekly':        
            # Last 7 days
            start_date = today - timedelta(days=7)
            date_trunc = TruncDate('created_at')
            date_format = '%Y-%m-%d'
        elif filter_type == 'yearly':
            start_date = today - timedelta(days=365)
            date_trunc = TruncMonth('created_at')
            date_format = '%Y-%m'
        else:  # monthly (default)
            start_date = today - timedelta(days=30)
            date_trunc = TruncDate('created_at')
            date_format = '%Y-%m-%d'
        
        # Get the sales data
        raw_sales_data = Order.objects.filter(
            created_at__gte=start_date,
            order_status='DELIVERED'
        ).annotate(
            date=date_trunc
        ).values('date').annotate(
            total_sales=Sum('total_amount')
        ).order_by('date')
        
        # Format the data for the frontend
        sales_data = []
        labels = []
        values = []
        
        for entry in raw_sales_data:
            date_str = entry['date'].strftime(date_format)
            sales_data.append({
                'date': date_str,
                'total_sales': float(entry['total_sales'] or 0)
            })
            labels.append(date_str)
            values.append(float(entry['total_sales'] or 0))
        
        return JsonResponse({
            'sales_data': sales_data,
            'labels': labels,
            'values': values
        })
    except Exception as e:
        logger.error(f'Error in get_sales_data: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch sales data', 'details': str(e)}, status=500)

@login_required(login_url='adminLogin')
def get_top_products(request):
    try:
        # Check if your model uses 'product' or 'variant__product'
        # Adjust the field names based on your actual model structure
        top_products = OrderItem.objects.filter(
            product__name__isnull=False,  # Filter out null product names
            product__name__gt=''  # Filter out empty product names
        ).values(
            'product__name'  # Assuming direct relationship with product
        ).annotate(
            units_sold=Sum('quantity'),
            revenue=Sum('price')
        ).order_by('-revenue')[:10]
        
        products_list = []
        for product in top_products:
            product_name = product.get('product__name')
            products_list.append({
                'name': product_name,
                'units_sold': product['units_sold'],
                'revenue': float(product['revenue'] if product['revenue'] else 0)
            })
        
        return JsonResponse({
            'products': products_list
        })
    except Exception as e:
        logger.error(f'Error in get_top_products: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch top products', 'details': str(e)}, status=500)

@login_required(login_url='adminLogin')
def get_top_categories(request):
    try:
        # Check if your model uses 'product__category' or 'variant__product__category'
        top_categories = OrderItem.objects.filter(
            product__category__name__isnull=False,  # Filter out null category names
            product__category__name__gt=''  # Filter out empty category names
        ).values(
            'product__category__name'  # Adjust this field based on your model structure
        ).annotate(
            units_sold=Sum('quantity'),
            revenue=Sum('price')
        ).order_by('-revenue')[:10]
        
        categories_list = []
        labels = []
        values = []
        
        for category in top_categories:
            category_name = category.get('product__category__name')
            
            categories_list.append({
                'name': category_name,
                'units_sold': category['units_sold'],
                'revenue': float(category['revenue'] if category['revenue'] else 0)
            })
            labels.append(category_name)
            values.append(float(category['revenue'] if category['revenue'] else 0))
        
        return JsonResponse({
            'categories': categories_list,
            'labels': labels,
            'values': values
        })
    except Exception as e:
        logger.error(f'Error in get_top_categories: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch top categories', 'details': str(e)}, status=500)

@login_required(login_url='adminLogin')
def get_top_brands(request):
    try:
        top_brands = OrderItem.objects.filter(
            product__brand__name__isnull=False,  # Filter out null brand names
            product__brand__name__gt=''  # Filter out empty brand names
        ).values(
            'product__brand__name'  # Adjust this field based on your model structure
        ).annotate(
            units_sold=Sum('quantity'),
            revenue=Sum('price')
        ).order_by('-revenue')[:10]
        
        brands_list = []
        labels = []
        values = []
        
        for brand in top_brands:
            brand_name = brand.get('product__brand__name')
            
            brands_list.append({
                'name': brand_name,
                'units_sold': brand['units_sold'],
                'revenue': float(brand['revenue'] if brand['revenue'] else 0)
            })
            labels.append(brand_name)
            values.append(float(brand['revenue'] if brand['revenue'] else 0))
        
        return JsonResponse({
            'brands': brands_list,
            'labels': labels,
            'values': values
        })
    except Exception as e:
        logger.error(f'Error in get_top_brands: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch top brands', 'details': str(e)}, status=500)

@login_required(login_url='adminLogin')
def get_products(request):
    try:
        search = request.GET.get('search', '')
        page = request.GET.get('page', 1)
        page_size = request.GET.get('per_page', 10)
        
        # Filter products based on search query if provided
        products_query = Product.objects.all().order_by('id')
        if search:
            products_query = products_query.filter(name__icontains=search)
        
        # Set up pagination
        paginator = Paginator(products_query, page_size)
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)
        
        # Prepare data for JSON response
        products_data = []
        for product in products_page:
            variants = product.variants.all()
            
            # Calculate total stock across all variants and sizes
            total_stock = 0
            price = 0
            for variant in variants:
                for size in variant.sizes.all():
                    total_stock += size.stock
                if variant.price and (price == 0 or variant.price < price):
                    price = variant.price
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'category': product.category.name if product.category else "N/A",
                'brand': product.brand.name if product.brand else "N/A",
                'price': float(price) if price else 0,
                'stock': total_stock,
                'is_active': product.is_active,
            })
        
        # Create response with pagination metadata
        response_data = {
            'items': products_data,
            'page': products_page.number,
            'total_pages': paginator.num_pages,
            'total': paginator.count,
            'has_next': products_page.has_next(),
            'has_previous': products_page.has_previous(),
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'Error in get_products: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch products', 'details': str(e)}, status=500)

@login_required(login_url='adminLogin')
def get_order_status_summary(request):
    try:
        status_counts = Order.objects.values('order_status').annotate(count=Count('id'))
        summary = {
            'PENDING': 0,
            'PROCESSING': 0,
            'SHIPPED': 0,
            'DELIVERED': 0,
            'CANCELLED': 0
        }
        
        for status_count in status_counts:
            status = status_count['order_status']
            if status in summary:
                summary[status] = status_count['count']
        
        return JsonResponse(summary)
    except Exception as e:
        logger.error(f'Error in get_order_status_summary: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch order status summary'}, status=500)

@login_required(login_url='adminLogin')
def get_recent_orders(request):
    try:
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
        orders_list = []
        
        for order in recent_orders:
            orders_list.append({
                'order_id': order.order_id,
                'customer_name': order.user.username if order.user else 'Unknown',
                'total_amount': float(order.total_amount) if order.total_amount else 0
            })
        
        return JsonResponse({'orders': orders_list})
    except Exception as e:
        logger.error(f'Error in get_recent_orders: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch recent orders'}, status=500)

@login_required(login_url='adminLogin')
def get_low_stock_products(request):
    try:
        # Fetch products with low stock
        products_list = []
        products = Product.objects.select_related('category').all()
        
        for product in products:
            total_stock = 0
            # Calculate total stock across all variants and sizes
            for variant in product.variants.all():
                for size in variant.sizes.all():
                    total_stock += size.stock
            
            # Show products with 20 or fewer units in stock
            if total_stock <= 20:
                products_list.append({
                    'name': product.name,
                    'category': product.category.name if product.category else 'N/A',
                    'stock': total_stock
                })
        
        # Sort by stock (lowest first)
        products_list.sort(key=lambda x: x['stock'])
        
        return JsonResponse({'products': products_list[:15]})  # Return top 15 low stock items
    except Exception as e:
        logger.error(f'Error in get_low_stock_products: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch low stock products'}, status=500)