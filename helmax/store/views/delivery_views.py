from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(['POST'])
def get_delivery_charge_api(request):
    """API endpoint to calculate delivery charge based on address."""
    try:
        data = json.loads(request.body)
        address_id = data.get('address_id')
        
        if not address_id:
            return JsonResponse({
                'success': False,
                'message': 'Address ID is required'
            })
        
        # Get the address
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Address not found'
            })
        
        # Get cart total if available
        cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
        order_amount = cart.final_price if cart else 0
        
        # Create location dictionary from address
        location = {
            'city': address.city.lower() if address.city else '',
            'state': address.state.lower() if address.state else '',
            'country': 'india',  # Default for now
        }
        
        # Calculate delivery charge
        from .delivery_charges import get_delivery_charge
        charge = get_delivery_charge(location, order_amount)
        
        return JsonResponse({
            'success': True,
            'charge': charge,
            'message': 'Delivery charge calculated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error calculating delivery charge: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Error calculating delivery charge'
        }, status=500)