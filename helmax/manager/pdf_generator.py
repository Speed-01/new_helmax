from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.utils import timezone

def generate_sales_report_pdf(response, orders, total_orders, total_sales, total_discounts, start_date, end_date):
    """
    Generate a professional PDF sales report with proper formatting and Rupee symbol
    """
    # Create PDF document with margins
    doc = SimpleDocTemplate(response, pagesize=letter, 
                          topMargin=30, bottomMargin=30, 
                          leftMargin=30, rightMargin=30)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add company header
    elements.append(Paragraph('HELMAX', title_style))
    elements.append(Paragraph('Premium Helmets', heading_style))
    elements.append(Paragraph('www.helmax.store | support@helmax.store | +91 8590065000', normal_style))
    elements.append(Paragraph('GST: 29AABCH1234R1Z5', normal_style))
    elements.append(Spacer(1, 20))  # Add space
    
    # Add report title
    elements.append(Paragraph(f'Sales Report ({start_date} to {end_date})', heading_style))
    elements.append(Paragraph(f'Generated on: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}', normal_style))
    elements.append(Spacer(1, 15))  # Add space
    
    # Add summary in a better format
    summary_data = [
        ['Summary', ''],
        ['Total Orders:', f'{total_orders}'],
        ['Total Sales:', f'₹{total_sales}'],
        ['Total Discounts:', f'₹{total_discounts}']
    ]
    summary_table = Table(summary_data, colWidths=[150, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('SPAN', (0, 0), (1, 0)),  # Span the header cell
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 8),
        ('BACKGROUND', (0, 1), (1, 3), colors.white),
        ('GRID', (0, 0), (1, 3), 1, colors.black),
        ('ALIGN', (1, 1), (1, 3), 'RIGHT')
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))  # Add space
    
    # Add detailed report heading
    elements.append(Paragraph('Detailed Order Report', heading_style))
    elements.append(Spacer(1, 10))  # Add space
    
    # Create table data
    data = [
        ['Order ID', 'Date', 'Customer', 'Items', 'Subtotal (₹)', 'Discount (₹)', 'Total (₹)', 'Status']
    ]
    for order in orders:
        data.append([
            order.order_id,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.user.username,
            order.order_items.count(),
            f'{float(order.total_amount):.2f}',
            f'{float(order.total_discount):.2f}',
            f'{float(order.total_amount):.2f}',
            order.order_status
        ])
    
    # Create and style the table with better formatting
    table = Table(data, repeatRows=1)  # Repeat header row on each page
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),  # Darker header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        
        # Alignment for specific columns
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Order ID left aligned
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Date centered
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),  # Customer left aligned
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),  # Items centered
        ('ALIGN', (4, 0), (6, -1), 'RIGHT'),  # Money columns right aligned
        ('ALIGN', (7, 0), (7, -1), 'CENTER'),  # Status centered
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Thicker line below header
        
        # Zebra striping for better readability
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    elements.append(table)
    
    # Add footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph('This is an official document generated by Helmax ERP System.', normal_style))
    elements.append(Paragraph('For any queries, please contact accounts@helmax.com', normal_style))
    
    # Build PDF
    doc.build(elements)
    return response
