from .models import ReturnRequest, Order

def admin_context(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return {
            'pending_returns_count': ReturnRequest.objects.filter(status='PENDING').count(),
            'pending_orders_count': Order.objects.filter(order_status='PENDING').count()
        }
    return {}