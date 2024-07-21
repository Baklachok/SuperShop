from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BasketViewSet, UpdateBasketItemView, AddToBasketView, FavouritesViewSet

app_name = 'purchases'

router = DefaultRouter()
router.register(r'favourites', FavouritesViewSet, basename='favourites')

urlpatterns = [
    path('baskets/', BasketViewSet.as_view({'get': 'list'})),

    path('baskets/add/', AddToBasketView.as_view(), name='add-to-cart'),
    path('baskets/basket-item/<int:item_id>/', UpdateBasketItemView.as_view(), name='update-cart-item'),
    path('', include(router.urls)),

]
