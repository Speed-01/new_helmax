from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Product, Variant

from .models import Product, Variant




User = get_user_model()
 

class SignupForm(UserCreationForm):
    email = forms.EmailField(
        max_length=255, 
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-black bg-opacity-50 text-white border border-gray-600 rounded-md p-3 focus:outline-none focus:border-yellow-500',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=10, 
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-black bg-opacity-50 text-white border border-gray-600 rounded-md p-3 focus:outline-none focus:border-yellow-500',
            'placeholder': 'Phone Number'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-black bg-opacity-50 text-white border border-gray-600 rounded-md p-3 focus:outline-none focus:border-yellow-500',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-black bg-opacity-50 text-white border border-gray-600 rounded-md p-3 focus:outline-none focus:border-yellow-500',
            'placeholder': 'Last Name'
        })
    )

    class Meta:
        model = User  
        fields = ['first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("User with this Email already exists.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise ValidationError("Enter a valid 10-digit phone number.")
        return phone
    
    
    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
    
    
        if first_name and last_name:
            full_name = f"{first_name} {last_name}".strip()  
           
            if User.objects.filter(first_name=first_name, last_name=last_name).exists():
                raise ValidationError("A user with this name already exists.")
        return cleaned_data
    
class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, required=True, label="Enter OTP")

    def clean_otp(self):
        otp = self.cleaned_data['otp']
        if not otp.isdigit() or len(otp) != 6:
            raise forms.ValidationError("OTP must be a 6-digit number.")
        return otp


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254)

class SetPasswordForm(forms.Form):
    password1 = forms.CharField(label='New Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
        return cleaned_data




# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
#         fields = ['name', 'category']  # Removed price and stock as they are part of the Variant model
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#         }

#     def clean_name(self):
#         name = self.cleaned_data.get('name')
#         if not name or not re.search(r'\w', name):
#             raise ValidationError("Name cannot be empty, symbols only, or spaces only.")
#         return name

#     def clean_description(self):
#         description = self.cleaned_data.get('description')
#         if not description or not re.search(r'\w', description):
#             raise ValidationError("Description cannot be empty, symbols only, or spaces only.")
#         return description


# class AddProductForm(forms.ModelForm):
    
#     class Meta:
#         model = Product
#         fields = ['name', 'category', 'description', ]
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter product description', 'rows': 3}),
            
#         }

#     def clean_name(self):
#         name = self.cleaned_data.get('name')
#         if not name or not re.search(r'\w', name):
#             raise ValidationError("Name cannot be empty, symbols only, or spaces only.")
#         return name

#     def clean_description(self):
#         description = self.cleaned_data.get('description')
#         if not description or not re.search(r'\w', description):
#             raise ValidationError("Description cannot be empty, symbols only, or spaces only.")
#         return description


# class ProductVariantForm(forms.ModelForm):
    
#     class Meta:
#         model = Variant
#         fields = ['price', 'color', 'stock', 'size', 'discount_price']
#         widgets = {
#             'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price', 'required': 'True', 'min': 0}),
#             'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity', 'required': 'True', 'min': 0}),
#             'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter size (e.g., S, M, L, XL)'}),
#             'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount price', 'min': 0}),
#             'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter color (e.g., Red, Blue)'}),
#         }

#     def clean_price(self):
#         price = self.cleaned_data.get('price')
#         if price is None:
#             raise ValidationError("Price cannot be empty")
#         if price < 0:
#             raise ValidationError("Price cannot be negative.")
#         return price

#     def clean_stock(self):
#         stock = self.cleaned_data.get('stock', 0)  # Default to 0 if stock is None
#         if stock < 0:
#             raise ValidationError("Quantity cannot be negative.")
#         return stock

#     def clean(self):
#         cleaned_data = super().clean()
#         price = cleaned_data.get('price')
#         discount_price = cleaned_data.get('discount_price')
#         if price is not None and discount_price is not None and discount_price >= price:
#             raise ValidationError("Discount price must be less than the original price.")
#         return cleaned_data
