from django.urls import path
from . import views
from . import invoice_views


urlpatterns = [
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('', views.login, name='Login'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout, name='logout'),
    path('confirm-logout/', views.confirm_logout, name='confirm_logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('search/', views.product_search, name='product_search'),
   
    # path('auth-receiver/', views.auth_receiver, name='auth_receiver'),



    path('api/filter-products/', views.filter_products, name='filter_products'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/variant/<int:variant_id>/', views.get_variant_data, name='get_variant_data_with_product'),
    
    path('user-profile/<int:user_id>/', views.user_profile, name='user_profile'),
    # path('edit-profile/', views.edit_user_profile, name='edit_user_profile'),



    ######## CART ########  
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_quantity, name='update_quantity'),
    path('cart/get-totals/', views.get_cart_totals, name='get_cart_totals'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('validate-cart/', views.validate_cart, name='validate_cart'),

    ######### Address ########
    path('userManageAddress/', views.userManageAddress, name='userManageAddress'),
    path('editAddress/<int:address_id>/', views.editAddress, name='editAddress'),
    path('deleteAddress/<int:address_id>/', views.deleteAddress, name='deleteAddress'),
    path('set_primary_address/', views.set_primary_address, name='set_primary_address'),
    path('add_address_checkout/', views.add_address_checkout, name='add_address_checkout'),


    ######### cheout ######## 
    path('checkout/', views.user_checkout, name='user_checkout'),

    path('place-order/', views.place_order, name='place_order'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-details/<str:order_id>/', views.order_details, name='order_details'),
    path('download-invoice/<str:order_id>/', views.download_invoice, name='download_invoice'),

        ########### Wishlist ########
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('move-to-wishlist/<int:variant_id>/', views.move_to_wishlist, name='move_to_wishlist'),
    path('remove-from-wishlist/<int:variant_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('clear-wishlist/', views.clear_wishlist, name='clear_wishlist'),
    path('add-multiple-to-cart/', views.add_multiple_to_cart, name='add_multiple_to_cart'),
    path('api/product/<int:product_id>/', views.product_detail, name='get_product_details'),
    path('api/variant/<int:variant_id>/sizes/', views.get_variant_data, name='get_variant_data'),
    path('sort-wishlist/<str:sort_by>/', views.sort_wishlist, name='sort_wishlist'),
    path('api/similar-products/', views.load_similar_products, name='load_similar_products'),
    # urls.py
    
    path('coupons/', views.available_coupons, name='available_coupons'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('cart/check-coupon/', views.check_coupon, name='check_coupon'),
    path('orders/create/', views.create_order, name='create_order'),

    # path('payment/callback/', views.payment_callback, name='payment_callback'),
    # path('payment/webhook/', views.payment_webhook, name='payment_webhook'),
    path('api/filter-products/', views.filter_products, name='filter_products'),
    path('payment/success/<str:order_id>/', views.payment_success, name='payment_success'),
    path('payment/retry/<str:order_id>/', views.retry_payment, name='retry_payment'),
    path('retry-payment-form/<str:order_id>/', views.retry_payment_form, name='retry_payment_form'),
    path('payment/check-status/<str:order_id>/', views.payment_success, name='check_payment_status'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('api/order-items/<int:item_id>/return/', views.create_return_request, name='create_return_request'),
    path('orders/<int:order_id>/detail/', views.order_detail, name='order_detail'),
    path('api/orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/items/<int:item_id>/return/', views.create_return_request, name='create_return_request'),
    path('order-details/<str:order_id>/', views.order_details, name='order_details'),
    path('download-invoice/<str:order_id>/', views.download_invoice, name='download_invoice'),
    
    ######### Reviews ########
    path('review/submit/<int:order_item_id>/', views.submit_review, name='submit_review'),
    path('review/helpful/<int:review_id>/', views.mark_review_helpful, name='mark_review_helpful'),
    path('api/reviews/<int:product_id>/', views.get_product_reviews, name='get_product_reviews'),
]