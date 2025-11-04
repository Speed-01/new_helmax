from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect 
from django.urls import reverse

class NoCacheMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
class AdminLoginRequiredMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        login_url = reverse('adminLogin')
        #excluding the admin login to prevent the redirect loop
        if request.path == login_url:
            return None
        # If the requested URL is part of the /manager/ section and the user is not logged in,
        # redirect them to the admin login page to enforce authentication and prevent unauthorized access.
        if request.path.startswith('/manager/') and not request.user.is_authenticated:
            return redirect('adminLogin')
        return None