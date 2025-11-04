from django.core.mail import send_mail
from django.conf import settings

from django.utils import timezone


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

    for item in order.orderitem_set.all():
        y -= 20
        p.drawString(120, y, f"{item.product.name} x {item.quantity} — ₹{item.price}")

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
