from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from store.models import Order

@login_required
def get_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Force refresh from database to get latest status
    order.refresh_from_db()
    
    # Get the latest status timestamp and use it as cache buster
    latest_timestamp = max(
        filter(None, [
            order.created_at,
            order.confirmed_at,
            order.processed_at,
            order.shipped_at,
            order.delivered_at,
            order.cancelled_at
        ])
    )
    
    # Add cache control headers and force status refresh
    response = JsonResponse({
        'success': True,
        'order_status': order.get_order_status_display(),
        'timeline': get_order_timeline(order),
        'timestamp': latest_timestamp.timestamp()
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_order_timeline(order):
    # Ensure we get the latest order data
    order.refresh_from_db()
    
    timeline = []
    
    # Add events to timeline
    if order.created_at:
        timeline.append({
            'status': 'Order Placed',
            'date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'Order #{order.order_number} has been placed successfully'
        })
    
    if order.confirmed_at:
        timeline.append({
            'status': 'Order Confirmed',
            'date': order.confirmed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Your order has been confirmed and is being processed'
        })
    
    if order.processed_at:
        timeline.append({
            'status': 'Processing',
            'date': order.processed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Your order is being prepared for shipping'
        })
    
    if order.shipped_at:
        timeline.append({
            'status': 'Shipped',
            'date': order.shipped_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'Your order has been shipped via {order.shipping_carrier}. Tracking number: {order.tracking_number}'
        })
    
    if order.delivered_at:
        timeline.append({
            'status': 'Delivered',
            'date': order.delivered_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Your order has been delivered successfully'
        })
    
    # Sort timeline by date in descending order to show latest events first
    timeline.sort(key=lambda x: x['date'], reverse=True)
    
    return timeline