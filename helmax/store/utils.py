from django.core.mail import send_mail
from django.conf import settings

from django.utils import timezone

def send_otp_email(email, otp, purpose="signup"):
    """
    Send OTP email for signup or password reset
    """
    if purpose == "signup":
        subject = "Welcome to Helmax - Verify Your Email Address"
        message = f"""Hello,

Thank you for signing up with Helmax!

To complete your registration, please use the following One-Time Password (OTP):

    {otp}

This OTP is valid for 1 minute only.

If you did not request this registration, please ignore this email.

Best regards,
The Helmax Team
"""
    else:  
        subject = "Helmax - Password Reset Request"
        message = f"""Hello,

We received a request to reset your password for your Helmax account.

Please use the following One-Time Password (OTP) to reset your password:

    {otp}

This OTP is valid for 1 minute only.

If you did not request a password reset, please ignore this email or contact support if you have concerns.

Best regards,
The Helmax Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
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
    items = order.order_items.all()
    items.update(status=new_status)
    
    # Also update the timestamp for each item
    if new_status in timestamp_fields:
        timestamp_field = timestamp_fields[new_status]
        current_time = timezone.now()
        for item in items:
            setattr(item, timestamp_field, current_time)
            item.save()
    
    # Send notification to customer
    send_order_status_notification(order)

def send_order_status_notification(order):
    """Send email notification about order status change"""
    subject = f'Order #{order.order_id} Status Update'
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

    )

from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas

def generate_invoice_pdf(order):
    """
    Generates a PDF invoice for a given order object.
    Returns an HttpResponse with the PDF file content.
    """

    # Create a file-like buffer to receive PDF data.
    buffer = BytesIO()

    # Create the PDF object using ReportLab.
    p = canvas.Canvas(buffer)

    # Write invoice header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 800, "INVOICE")

    # Write order details
    p.setFont("Helvetica", 12)
    p.drawString(100, 760, f"Order ID: {order.id}")
    p.drawString(100, 740, f"Customer: {order.user.username}")
    p.drawString(100, 720, f"Total Amount: ₹{order.total_amount}")

    y = 680
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Items:")
    p.setFont("Helvetica", 12)

    # Access related order items using the related_name defined on OrderItem
    # In models.OrderItem the ForeignKey has related_name='order_items', so
    # use order.order_items.all(). If that attribute is missing for any reason,
    # fall back to the default reverse manager orderitem_set.
    try:
        items_qs = order.order_items.all()
    except Exception:
        try:
            items_qs = order.orderitem_set.all()
        except Exception:
            items_qs = []

    if not items_qs:
        y -= 20
        p.drawString(120, y, "(No items found for this order)")
    else:
        for item in items_qs:
            y -= 20
            product_name = getattr(item.product, 'name', 'Unknown product')
            qty = getattr(item, 'quantity', 0)
            price = getattr(item, 'price', 0)
            p.drawString(120, y, f"{product_name} x {qty} — ₹{price}")

    # Finalize the PDF
    p.showPage()
    p.save()

    # Get the value from the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Return a response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    return response
