from django.urls import path, include
from rest_framework.routers import DefaultRouter

from user_profile.views import AddressViewSet

app_name='user_profile'

router = DefaultRouter()
router.register(r'addresses', AddressViewSet)

urlpatterns = [
    path('', include(router.urls)),
]