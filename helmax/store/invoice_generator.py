from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from django.conf import settings
import os
from datetime import datetime


def _get_static_logo_path():
    """Try to locate a site logo in the project's static files.
    Returns None if not found.
    """
    try:
        static_dirs = getattr(settings, 'STATICFILES_DIRS', [])
        for d in static_dirs:
            candidate = os.path.join(d, 'images', 'helmax-logo.png')
            if os.path.exists(candidate):
                return candidate
            candidate2 = os.path.join(d, 'images', 'logo2.png')
            if os.path.exists(candidate2):
                return candidate2
    except Exception:
        pass
    # try STATIC_ROOT as fallback
    try:
        candidate = os.path.join(settings.STATIC_ROOT or '', 'images', 'helmax-logo.png')
        if os.path.exists(candidate):
            return candidate
    except Exception:
        pass
    return None


def _money(v):
    try:
        return f'₹{float(v):,.2f}'
    except Exception:
        return f'₹{v}'


def generate_invoice_pdf(order):
    """
    Create a nicely formatted invoice PDF and return the filename saved under MEDIA_ROOT/invoices/.
    """
    filename = f'invoice_{order.order_id}.pdf'
    filepath = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    normal = styles['Normal']
    heading = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, leading=16)
    elems = []

    # Header: logo + company info
    logo_path = _get_static_logo_path()
    if logo_path:
        try:
            im = Image(logo_path, width=1.2 * inch, height=1.2 * inch)
        except Exception:
            im = None
    else:
        im = None

    company_info = [
        Paragraph('<b>HELMAX</b>', heading),
        Paragraph('Motorcycle Gear & Accessories', normal),
        Paragraph('support@helmax.example', normal),
        Paragraph('+91 99999 99999', normal),
        Paragraph('www.helmax.example', normal)
    ]

    # Build header table
    header_data = []
    if im:
        header_data.append([im, company_info])
    else:
        header_data.append(['', company_info])

    header_table = Table(header_data, colWidths=[1.4 * inch, 4.6 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    elems.append(header_table)
    elems.append(Spacer(1, 12))

    elems.append(Paragraph('<b>INVOICE</b>', styles['Title']))
    elems.append(Spacer(1, 6))

    # Invoice & billing info
    invoice_meta = [
        ['Invoice ID:', order.order_id],
        ['Date:', order.created_at.strftime('%Y-%m-%d') if getattr(order, 'created_at', None) else datetime.now().strftime('%Y-%m-%d')],
        ['Payment Method:', getattr(order.payment_method, 'name', 'N/A')],
    ]

    billing = [
        ['Bill To:', ''],
        ['Name:', order.full_name or (order.user.get_full_name() if hasattr(order.user, 'get_full_name') else order.user.username)],
        ['Email:', order.email or getattr(order.user, 'email', '')],
        ['Phone:', order.phone or ''],
        ['Address:', f"{order.address_line1 or ''} {order.address_line2 or ''} {order.city or ''} {order.state or ''} {order.pincode or ''}"]
    ]

    meta_table = Table([[Paragraph('<b>Invoice Details</b>', normal), ''], [
        Table(invoice_meta, colWidths=[1.2 * inch, 2.8 * inch], hAlign='LEFT'),
        Table(billing, colWidths=[1.0 * inch, 3.0 * inch], hAlign='LEFT')
    ]], colWidths=[3.0 * inch, 3.0 * inch])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('INNERGRID', (0, 1), (-1, -1), 0.25, colors.white),
        ('BOX', (0, 1), (-1, -1), 0.25, colors.white),
    ]))

    elems.append(meta_table)
    elems.append(Spacer(1, 12))

    # Items table header
    table_data = [[
        Paragraph('<b>Item</b>', normal),
        Paragraph('<b>Variant</b>', normal),
        Paragraph('<b>Qty</b>', normal),
        Paragraph('<b>Unit Price</b>', normal),
        Paragraph('<b>Total</b>', normal)
    ]]

    items = list(order.order_items.all())
    if not items:
        table_data.append(['(No items)', '', '', '', ''])
    else:
        for it in items:
            desc = getattr(it.variant.product, 'name', 'Unknown product') if getattr(it, 'variant', None) else getattr(it.product, 'name', 'Unknown product')
            variant = getattr(it.variant, 'color', '') if getattr(it, 'variant', None) else ''
            qty = getattr(it, 'quantity', 0)
            unit = getattr(it, 'price', 0)
            try:
                total = qty * float(unit or 0)
            except Exception:
                total = 0
            table_data.append([
                Paragraph(desc, normal),
                Paragraph(str(variant), normal),
                str(qty),
                _money(unit),
                _money(total)
            ])

    # Totals
    subtotal = sum((it.quantity or 0) * float(it.price or 0) for it in items)
    product_discount = float(getattr(order, 'product_discount', 0) or 0)
    coupon_discount = float(getattr(order, 'coupon_discount', 0) or 0)
    total_discount = product_discount + coupon_discount
    final_amount = subtotal - total_discount

    # Add the totals rows as separate table to align right
    items_table = Table(table_data, colWidths=[3.0 * inch, 1.2 * inch, 0.6 * inch, 1.0 * inch, 1.0 * inch])
    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    elems.append(items_table)
    elems.append(Spacer(1, 12))

    totals_data = [
        ['', '', Paragraph('<b>Subtotal</b>', normal), Paragraph(_money(subtotal), normal)],
        ['', '', Paragraph('<b>Product Discount</b>', normal), Paragraph(_money(product_discount), normal)],
        ['', '', Paragraph('<b>Coupon Discount</b>', normal), Paragraph(_money(coupon_discount), normal)],
        ['', '', Paragraph('<b>Total</b>', styles['Heading2']), Paragraph(_money(final_amount), styles['Heading2'])]
    ]

    totals_table = Table(totals_data, colWidths=[3.0 * inch, 1.2 * inch, 1.0 * inch, 1.0 * inch])
    totals_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (0, 1), (1, 1)),
        ('SPAN', (0, 2), (1, 2)),
        ('SPAN', (0, 3), (1, 3)),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('RIGHTPADDING', (3, 0), (3, -1), 6),
    ]))

    elems.append(totals_table)
    elems.append(Spacer(1, 24))

    elems.append(Paragraph('Thank you for your purchase!', normal))
    elems.append(Spacer(1, 6))
    elems.append(Paragraph('If you have any questions about this invoice, please contact support@helmax.example', styles['Normal']))

    # Build PDF
    doc.build(elems)

    return filename