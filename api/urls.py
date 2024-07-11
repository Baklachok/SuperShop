from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rest_framework_nested.routers import NestedDefaultRouter

from api.views import ItemViewSet, CategoryViewSet, PhotoViewSet, ItemDetail

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'photos', PhotoViewSet)
router.register(r'items', ItemViewSet)

categories_router = NestedDefaultRouter(router, r'categories', lookup='category')
categories_router.register(r'items', ItemViewSet, basename='category-items')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(categories_router.urls)),
    # path('register/', UserRegistrationView.as_view(), name='register'),
]

urlpatterns += [
    path('categories/<slug:slug>/', CategoryViewSet.as_view({'get': 'retrieve'}), name='category-detail'),
    path('categories/<str:category_slug>/items/<int:item_id>/', ItemDetail.as_view(), name='item-detail'),
]