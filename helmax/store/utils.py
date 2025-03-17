from django.core.mail import send_mail
from django.conf import settings
<<<<<<< HEAD
from django.utils import timezone
=======
>>>>>>> e9bfa11a3ee794a710d4f72e0897ebafe185349a

def send_otp_email(email, otp, purpose="signup"):
    """
    Send OTP email for signup or password reset
    """
    if purpose == "signup":
        subject = "Your OTP for Signup in Helmax"
        message = f"Your OTP is {otp}. It is valid for 1 minutes."
    else:  
        subject = "Password Reset OTP"
        message = f"Your OTP for password reset is {otp}. Valid for 1 minutes."

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
<<<<<<< HEAD
    )

def update_order_status(order, new_status):
    """Update order status and set corresponding timestamp"""
    timestamp_fields = {
        'CONFIRMED': 'confirmed_at',
        'PROCESSING': 'processed_at',
        'SHIPPED': 'shipped_at',
        'DELIVERED': 'delivered_at',
        'CANCELLED': 'cancelled_at'
    }
    
    if new_status in timestamp_fields:
        setattr(order, timestamp_fields[new_status], timezone.now())
    
    order.order_status = new_status
    order.save()
    
    # Update all order items
    order.order_items.all().update(status=new_status)
    
    # Send notification to customer
    send_order_status_notification(order)

def send_order_status_notification(order):
    """Send email notification about order status change"""
    subject = f'Order #{order.order_number} Status Update'
    message = f'Your order status has been updated to: {order.get_order_status_display()}'
    
    if order.tracking_number and order.order_status == 'SHIPPED':
        message += f'\nTracking Number: {order.tracking_number}'
        message += f'\nShipping Carrier: {order.shipping_carrier}'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        fail_silently=True
=======
>>>>>>> e9bfa11a3ee794a710d4f72e0897ebafe185349a
    )