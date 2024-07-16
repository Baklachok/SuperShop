from django.urls import path
from .views import BasketViewSet, UpdateBasketItemView, AddToBasketView

app_name = 'purchases'

urlpatterns = [
    path('baskets/', BasketViewSet.as_view({'get': 'list'})),

    path('baskets/add/', AddToBasketView.as_view(), name='add-to-cart'),
    path('baskets/basket-item/<int:item_id>/', UpdateBasketItemView.as_view(), name='update-cart-item'),

]
