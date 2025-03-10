from django.urls import path

from . import views

from django.conf import settings

from django.conf.urls.static import static









urlpatterns = [

    

    path('', views.adminLogin, name='adminLogin'),

    path('logout/', views.admin_logout, name='admin_logout'),

    #path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    

    

    path('customers/', views.customers, name='customers'),

    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

    

    

    path('adminProducts/', views.adminProducts, name='adminProducts'),

    path('addProducts/', views.addProducts, name='addProducts'),

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







    path('admin_orders/', views.admin_orders, name='admin_orders'),

    path('admin_orders/api/', views.admin_orders_api, name='admin_orders_api'),

    path('order-detail/<int:order_id>/', views.order_detail, name='orderDetail'),

    path('update-order-status/<int:order_id>/', views.update_order_status, name='updateOrderStatus'),

    path('update-item-status/', views.update_item_status, name='updateItemStatus'),

    # path('handle-return-request/<int:return_id>/', views.handle_return_request, name='handleReturnRequest'),

    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    

    path('coupons/', views.admin_coupons, name='admin_coupons'),

    path('coupons/add/', views.add_coupon, name='add_coupon'),

    path('coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),

    path('coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),

    path('get-coupon/<int:coupon_id>/', views.get_coupon_details, name='get_coupon_details'),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)