from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from ..delivery_charges import reverse_geocode, get_delivery_charge, calculate_distance_based_charge

@ensure_csrf_cookie
@require_http_methods(['POST'])
def get_delivery_charge_view(request):
    """Handle delivery charge calculation based on user location."""
    try:
        data = request.POST
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        
        # Get location details from coordinates
        location = reverse_geocode(latitude, longitude)
        
        # Get cart total if available
        cart = request.user.cart_set.filter(is_ordered=False).first() if request.user.is_authenticated else None
        order_amount = cart.final_price if cart else 0
        
        # Calculate delivery charge based on location
        location_str = f"{location.city}, {location.state}" if location.city and location.state else \
                      location.city or location.state or ''
        
        result = get_delivery_charge(location_str, order_amount)
        
        # Calculate distance-based charge as fallback
        if not result.charge:
            store_coords = (10.0261, 76.3125)  # Default store coordinates (Kaniyapuram)
            distance_result = calculate_distance_based_charge((latitude, longitude), store_coords)
            result.charge = distance_result['charge']
            result.message = distance_result['message']
        
        return JsonResponse({
            'success': True,
            'charge': result.charge,
            'message': result.message,
            'location': {
                'city': location.city,
                'state': location.state,
                'country': location.country
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error calculating delivery charge: {str(e)}'
        }, status=400)