from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BasketViewSet
app_name = 'purchases'

router = DefaultRouter()
router.register(r'baskets', BasketViewSet, basename='basket')

urlpatterns = [
    path('', include(router.urls)),
]
