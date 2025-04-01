from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from store import views
from manager import views as manager_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("store.urls")),
    path("manager/", include("manager.urls")),
    
    path('accounts/', include('allauth.urls')),  
    path('api/order-items/<int:item_id>/cancel/', views.cancel_order_item, name='cancel_order_item'),
    path('api/order-items/<int:item_id>/return/', views.create_return_request, name='create_return_request'),
    path('manager/return-requests/', manager_views.admin_return_requests, name='admin_return_requests'),
    path('manager/handle-return-request/<int:return_request_id>/', manager_views.handle_return_request, name='handle_return_request'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)