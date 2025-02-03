from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *



class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'phone', 'created_at', 'updated_at', 'referral_code', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'phone', 'referral_code')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')

models_to_register = [
    User,
    Category,
    Product,
    Brand,
    ProductImage,
    Variant,
    OTP,
    Size,
    Cart,
    PaymentMethod,
    CartItem,
    Profile,
    Order,
    OrderItem,
    ReturnRequest,
    Address,
    Wishlist
    
]
for model in models_to_register:
    admin.site.register(model)
