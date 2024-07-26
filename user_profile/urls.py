from django.urls import path, include
from rest_framework.routers import DefaultRouter

from user_profile.views import AddressViewSet, ReviewViewSet, ReviewPhotoViewSet

app_name='user_profile'

router = DefaultRouter()
router.register(r'addresses', AddressViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'review_photos', ReviewPhotoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]