from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OrdersViewSet

app_name = 'orders'

router = DefaultRouter()
router.register(r'orders', OrdersViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
