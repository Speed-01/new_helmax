from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from manager.models import Order
from .invoice_generator import generate_invoice_pdf
import os
from django.conf import settings

@login_required
def download_invoice(request, order_number):
    try:
        # Get the order and verify ownership
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        # Generate the invoice PDF
        filename = generate_invoice_pdf(order)
        
        # Prepare the file path
        file_path = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        
        raise Http404()
        
    except Exception as e:
        raise Http404(str(e))