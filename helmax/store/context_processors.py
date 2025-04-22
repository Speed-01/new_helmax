from django.conf import settings
from manager.models import Wishlist

def payment_context(request):
    context = {
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'wishlist_count': 0
    }
    
    if request.user.is_authenticated:
        try:
            wishlist, created = Wishlist.objects.get_or_create(user=request.user)
            context['wishlist_count'] = wishlist.variants.filter(
                is_active=True,
                product__is_active=True
            ).count()
        except Exception:
            pass
            
    return context