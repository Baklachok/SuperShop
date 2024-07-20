from django.urls import path
from .views import BasketViewSet, UpdateBasketItemView, AddToBasketView, CreatePaymentView, UpdatePaymentStatusView, \
    webhook_view

app_name = 'purchases'

urlpatterns = [
    path('baskets/', BasketViewSet.as_view({'get': 'list'})),

    path('baskets/add/', AddToBasketView.as_view(), name='add-to-cart'),
    path('baskets/basket-item/<int:item_id>/', UpdateBasketItemView.as_view(), name='update-cart-item'),
    path('payments/create/', CreatePaymentView.as_view(), name='create-payment'),
    path('payments/update-status/', UpdatePaymentStatusView.as_view(), name='update-payment-status'),
    path('webhooks/', webhook_view, name='webhook'),
]
