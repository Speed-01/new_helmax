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

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'payment_status', 'order_status', 'created_at')
    list_filter = ('payment_status', 'order_status', 'created_at')
    search_fields = ('id', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'payment_method')

# Remove these models from the general registration since they have custom admin classes
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
    OrderItem,
    ReturnRequest,
    Address,
]

# Register models without custom admin classes
for model in models_to_register:
    admin.site.register(model)

# Register models with custom admin classes
@admin.register(ProductOffer)
class ProductOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'product__name')
    date_hierarchy = 'start_date'

@admin.register(CategoryOffer)
class CategoryOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'category__name')
    date_hierarchy = 'start_date'

@admin.register(ReferralOffer)
class ReferralOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'referral_bonus', 'referee_bonus', 'usage_limit', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(ReferralUsage)
class ReferralUsageAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referee', 'offer', 'created_at', 'is_confirmed')
    list_filter = ('is_confirmed', 'created_at')
    search_fields = ('referrer__username', 'referee__username')
