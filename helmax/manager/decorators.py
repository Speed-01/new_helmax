from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.views.decorators.cache import never_cache
from django.http import HttpResponse

def admin_required(view_func):
    @wraps(view_func)
    @never_cache
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.warning(request, "You don't have admin access")
            response = redirect('adminLogin')
            # Add stronger cache control headers to prevent back button access
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['X-Frame-Options'] = 'DENY'
            # Clear any existing session data and cookies
            request.session.flush()
            request.session.clear_expired()
            response.delete_cookie('sessionid')
            response.delete_cookie('csrftoken')
            return response
            
        response = view_func(request, *args, **kwargs)
        if isinstance(response, HttpResponse):
            # Apply consistent cache control headers to all admin responses
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '-1'
            response['X-Frame-Options'] = 'DENY'
        return response
    return wrapper