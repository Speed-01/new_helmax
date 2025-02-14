from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from manager.models import User
from django.contrib.auth import login
from django.core.exceptions import MultipleObjectsReturned

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if user.id:
            return
        try:
            users = User.objects.filter(email=user.email)
            if users.count() > 1:
                # Handle the case where multiple users have the same email
                messages.error(request, "Multiple accounts found with the same email. Please contact support.")
                raise ImmediateHttpResponse(redirect('Login'))  # Redirect to an error page
            elif users.exists():
                # If exactly one user exists, connect the social account
                existing_user = users.first()
                sociallogin.connect(request, existing_user)
                login(request, existing_user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Your Google account has been connected to your existing account.')
                raise ImmediateHttpResponse(redirect('home'))
        except User.DoesNotExist:
            pass  # No action if the user doesn't exist, just continue
        except MultipleObjectsReturned:
            # Handle the case where multiple users with the same email exist
            messages.error(request, "Multiple accounts found with the same email. Please contact support.")
            raise ImmediateHttpResponse(redirect('Login'))