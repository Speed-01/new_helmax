from django.conf import settings
from manager.models import Wishlist

def get_cloudinary_defaults():
    cloud_name = getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME', '')
    return {
        'cloudinary_cloud_name': cloud_name,
        'default_product_image': f'https://res.cloudinary.com/{cloud_name}/image/upload/v1/default/no-product-image.jpg'
    }

def payment_context(request):
    context = {
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'wishlist_count': 0
    }
    # Add Cloudinary defaults
    context.update(get_cloudinary_defaults())
    
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
    