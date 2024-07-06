from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import ItemViewSet

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('register/', UserRegistrationView.as_view(), name='register'),
]