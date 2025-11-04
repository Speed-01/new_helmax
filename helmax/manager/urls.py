from django.urls import path
from . import views
from . import api
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # API endpoints for admin dashboard
    path('api/dashboard-metrics/', api.get_dashboard_metrics, name='api_dashboard_metrics'),
    path('api/sales-data/', api.get_sales_data, name='api_sales_data'),
    path('api/top-categories/', api.get_top_categories, name='api_top_categories'),
    path('api/top-products/', api.get_top_products, name='api_top_products'),
    path('api/top-brands/', api.get_top_brands, name='api_top_brands'),
    # Dashboard routes
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/data/', views.dashboard_data, name='dashboard_data'),
    
    # API routes for dashboard components
    path('get_top_products/', views.get_top_products, name='get_top_products'),
    path('get_top_categories/', views.get_top_categories, name='get_top_categories'),
    path('get_top_brands/', views.get_top_brands, name='get_top_brands'),
    
    # # Ledger generator
    # path('api/ledger-entries/', views.download_ledger, name='download_ledger'),

    path('', views.adminLogin, name='adminLogin'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('sales-report/', views.sales_report, name='sales_report'),
    
    path('customers/', views.customers, name='customers'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    
    path('adminProducts/', views.adminProducts, name='adminProducts'),
    path('addProducts/', views.addProducts, name='addProducts'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/brands/', views.api_brands, name='api_brands'),
    path('delete-product/<int:product_id>/', views.deleteProduct, name='deleteProduct'),
    path('delete-variant/<int:variant_id>/', views.deleteVariant, name='deleteVariant'),
    path('edit-product/<int:product_id>/', views.editProduct, name='editProduct'),
    path('edit-variant/<int:variant_id>/', views.editVariant, name='editVariant'),
    path('addVariant/<int:product_id>/', views.addVariant, name='addVariant'),
    path('toggle-product-status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
    path('toggle-variant/<int:variant_id>/', views.toggleVariant, name='toggleVariant'),

    path('admin_category/',views.admin_category,name="admin_category"),
    path('addcategory/',views.add_category,name="add_category"),
    path('edit_category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('toggle_category_status/<int:category_id>/', views.toggle_category_status, name='toggle_category_status'),

    path('search-products/', views.search_products, name='search_products'),
    
    path('admin_brands/', views.admin_brand, name='admin_brand'),
    path('admin_brands/add/', views.add_brand, name='add_brand'),
    path('admin_brands/edit/<int:brand_id>/', views.edit_brand, name='edit_brand'),
    path('admin_brands/toggle/<int:brand_id>/', views.toggle_brand_status, name='toggle_brand_status'),
    
    # Offer Management URLs
    path('get-product-offer/<int:offer_id>/', views.get_product_offer, name='get_product_offer'),
    path('get-category-offer/<int:offer_id>/', views.get_category_offer, name='get_category_offer'),

    path('admin_orders/', views.admin_orders, name='admin_orders'),
    path('admin_orders/api/', views.admin_orders_api, name='admin_orders_api'),
    path('order-detail/<str:order_id>/', views.order_detail, name='orderDetail'),
    path('update-order-status/<str:order_id>/', views.update_order_status, name='updateOrderStatus'),
    path('update-item-status/', views.update_item_status, name='updateItemStatus'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    
    path('coupons/', views.admin_coupons, name='admin_coupons'),
    path('coupons/add/', views.add_coupon, name='add_coupon'),
    path('coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('get-coupon/<int:coupon_id>/', views.get_coupon_details, name='get_coupon_details'),

    path('return-requests/', views.admin_return_requests, name='admin_return_requests'),
    path('api/return-requests/', views.get_return_requests, name='get_return_requests'),
    # Duplicate route with manager prefix for consistency with other API endpoints
    path('manager/api/return-requests/', views.get_return_requests, name='get_return_requests_alt'),
    # This URL is now defined in the project-level urls.py as 'manager/handle-return-request/<int:return_request_id>/'

    # Offer Management URLs
    path('offers/', views.admin_offers, name='admin_offers'),
    path('product-offers/', views.admin_product_offers, name='admin_product_offers'),
    path('product-offers/add/', views.add_product_offer, name='add_product_offer'),
    path('product-offers/<int:offer_id>/', views.get_product_offer, name='get_product_offer'),
    path('product-offers/edit/<int:offer_id>/', views.edit_product_offer, name='edit_product_offer'),
    path('product-offers/delete/<int:offer_id>/', views.delete_product_offer, name='delete_product_offer'),
    
    path('category-offers/', views.admin_category_offers, name='admin_category_offers'),
    path('category-offers/add/', views.add_category_offer, name='add_category_offer'),
    path('category-offers/<int:offer_id>/', views.get_category_offer, name='get_category_offer'),
    path('category-offers/edit/<int:offer_id>/', views.edit_category_offer, name='edit_category_offer'),
    path('category-offers/delete/<int:offer_id>/', views.delete_category_offer, name='delete_category_offer'),
    path('get-active-products/', views.get_active_products, name='get_active_products'),

    # Wallet Management URLs
    path('wallet/', views.admin_wallet, name='admin_wallet'),
    path('wallet/transaction/<int:transaction_id>/', views.admin_wallet_transaction_detail, name='admin_wallet_transaction_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)