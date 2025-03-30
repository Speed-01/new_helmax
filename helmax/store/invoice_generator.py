from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.conf import settings
import os

def generate_invoice_pdf(order):
    # Create the PDF file path in a temporary location
    filename = f'invoice_{order.order_number}.pdf'
    filepath = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Add company header
    elements.append(Paragraph('HELMAX', styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph('INVOICE', styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Add order information
    elements.append(Paragraph(f'Order Number: {order.order_number}', styles['Normal']))
    elements.append(Paragraph(f'Date: {order.created_at.strftime("%Y-%m-%d")}', styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Add customer information
    elements.append(Paragraph('Bill To:', styles['Heading2']))
    elements.append(Paragraph(f'Name: {order.user.get_full_name()}', styles['Normal']))
    elements.append(Paragraph(f'Email: {order.user.email}', styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Create table for order items
    table_data = [
        ['Item', 'Quantity', 'Price', 'Total']
    ]
    
    # Add order items to table
    for item in order.order_items.all():
        table_data.append([
            f'{item.variant.product.name} ({item.variant.color})',
            str(item.quantity),
            f'₹{item.price:.2f}',
            f'₹{(item.quantity * item.price):.2f}'
        ])
    
    # Add totals with proper discount handling
    subtotal = sum(item.quantity * item.price for item in order.order_items.all())
    product_discount = order.product_discount or 0
    coupon_discount = order.coupon_discount or 0
    total_discount = product_discount + coupon_discount
    final_amount = subtotal - total_discount

    table_data.extend([
        ['', '', 'Subtotal:', f'₹{subtotal:.2f}'],
        ['', '', 'Product Discount:', f'₹{product_discount:.2f}'],
        ['', '', 'Coupon Discount:', f'₹{coupon_discount:.2f}'],
        ['', '', 'Total:', f'₹{final_amount:.2f}']
    ])
    
    # Create and style the table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (-2, -3), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build the PDF document
    doc.build(elements)
    
    return filename