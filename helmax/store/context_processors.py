from django.conf import settings

def payment_context(request):
    return {
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    }