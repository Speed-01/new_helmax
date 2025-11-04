from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.utils.html import format_html
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
    list_display = ('order_id', 'user', 'total_amount', 'payment_status', 'order_status', 'created_at')
    list_filter = ('payment_status', 'order_status', 'created_at')
    search_fields = ('order_id', 'user__username', 'user__email')
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
    Address,
]

# Register models without custom admin classes
for model in models_to_register:
    admin.site.register(model)

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_order_id', 'get_customer_name', 'get_product_name', 'reason', 'status', 'created_at', 'action_buttons')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('order_item__order__order_id', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def get_order_id(self, obj):
        if not obj:
            return ''
        try:
            if obj.order_item:
                order = obj.order_item.order
                if order:
                    return order.order_id
            return 'No Order'
        except (AttributeError, Exception) as e:
            return 'Error: Unable to fetch order'
    get_order_id.short_description = 'Order ID'
    get_order_id.admin_order_field = 'order_item__order__order_id'
    
    def get_customer_name(self, obj):
        if not obj:
            return ''
        try:
            # First try to get username from the ReturnRequest's user field
            if obj.user:
                return obj.user.username
            # If that's not available, try to get it from the order
            if obj.order_item and obj.order_item.order:
                return obj.order_item.order.user.username
            return 'No Customer'
        except (AttributeError, Exception) as e:
            return 'Error: Unable to fetch customer'
    get_customer_name.short_description = 'Customer Name'
    get_customer_name.admin_order_field = 'user__username'
    
    def get_product_name(self, obj):
        if obj.order_item and obj.order_item.product:
            product_name = obj.order_item.product.name
            variant_info = f" - {obj.order_item.variant.color}" if obj.order_item.variant and obj.order_item.variant.color else ''
            size_info = f" - {obj.order_item.size.name}" if obj.order_item.size and obj.order_item.size.name else ''
            return f"{product_name}{variant_info}{size_info}"
        return 'No product information'
    get_product_name.short_description = 'Product'
    get_product_name.admin_order_field = 'order_item__product__name'
    
    def action_buttons(self, obj):
        if obj.status == 'PENDING':
            approve_url = reverse('admin:approve_return', args=[obj.pk])
            reject_url = reverse('admin:reject_return', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Approve</a>&nbsp;'
                '<a class="button" style="background-color: #ba2121;" href="{}">Reject</a>',
                approve_url, reject_url
            )
        elif obj.status == 'APPROVED':
            return format_html('<span style="color: green;">Approved</span>')
        elif obj.status == 'REJECTED':
            return format_html('<span style="color: red;">Rejected</span>')
        return ''
    action_buttons.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'approve/<int:return_id>/',
                self.admin_site.admin_view(self.approve_return),
                name='approve_return',
            ),
            path(
                'reject/<int:return_id>/',
                self.admin_site.admin_view(self.reject_return),
                name='reject_return',
            ),
        ]
        return custom_urls + urls
    
    def approve_return(self, request, return_id):
        return_request = ReturnRequest.objects.get(id=return_id)
        return_request.status = 'APPROVED'
        return_request.admin_response = 'Return request approved by admin.'
        return_request.save()
        
        # Update the order item status
        if return_request.order_item:
            return_request.order_item.return_status = 'APPROVED'
            return_request.order_item.save()
        
        self.message_user(request, f'Return request #{return_id} has been approved.')
        return HttpResponseRedirect(reverse('admin:manager_returnrequest_changelist'))
    
    def reject_return(self, request, return_id):
        return_request = ReturnRequest.objects.get(id=return_id)
        return_request.status = 'REJECTED'
        return_request.admin_response = 'Return request rejected by admin.'
        return_request.save()
        
        # Update the order item status
        if return_request.order_item:
            return_request.order_item.return_status = 'REJECTED'
            return_request.order_item.save()
        
        self.message_user(request, f'Return request #{return_id} has been rejected.')
        return HttpResponseRedirect(reverse('admin:manager_returnrequest_changelist'))

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
