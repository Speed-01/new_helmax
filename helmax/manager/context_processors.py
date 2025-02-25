from .models import ReturnRequest

def admin_context(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return {
            'pending_returns_count': ReturnRequest.objects.filter(status='PENDING').count()
        }
    return {} 