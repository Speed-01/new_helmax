from django.urls import path
from . import views


urlpatterns = [
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('', views.login, name='Login'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('search/', views.product_search, name='product_search'),
   
    # path('auth-receiver/', views.auth_receiver, name='auth_receiver'),



    path('api/filter-products/', views.filter_products, name='filter_products'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/variant/<int:variant_id>/', views.get_variant_data, name='get_variant_data'),
    
    path('user-profile/<int:user_id>/', views.user_profile, name='user_profile'),
    # path('edit-profile/', views.edit_user_profile, name='edit_user_profile'),



    ######## CART ########  
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_quantity, name='update_quantity'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('validate-cart/', views.validate_cart, name='validate_cart'),

    ######### Address ########
    path('userManageAddress/', views.userManageAddress, name='userManageAddress'),
    path('editAddress/<int:address_id>/', views.editAddress, name='editAddress'),
    path('deleteAddress/<int:address_id>/', views.deleteAddress, name='deleteAddress'),
    path('set_primary_address/', views.set_primary_address, name='set_primary_address'),


    ######### cheout ########
    path('checkout/', views.user_checkout, name='user_checkout'),


    path('place-order/', views.place_order, name='place_order'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

        ########### Wishlist ########
    path('wishlist/', views.wishlist_view, name='view_wishlist'),
    path('move-to-wishlist/<int:variant_id>/', views.move_to_wishlist, name='move_to_wishlist'),
    path('remove-from-wishlist/<int:variant_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    # urls.py
    path('api/orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('coupons/', views.available_coupons, name='available_coupons'),
    

    # path('payment/callback/', views.payment_callback, name='payment_callback'),
    # path('payment/webhook/', views.payment_webhook, name='payment_webhook'),
    path('api/filter-products/', views.filter_products, name='filter_products'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('wallet/', views.wallet_view, name='wallet'),
]