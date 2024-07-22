from django.urls import path, include
from .views import BasketViewSet, UpdateBasketItemView, AddToBasketView, CreatePaymentView, UpdatePaymentStatusView, \
    webhook_view, BasketItemDeleteView
from rest_framework.routers import DefaultRouter


app_name = 'purchases'

# router = DefaultRouter()
# router.register(r'favourites', FavouritesViewSet, basename='favourites')

urlpatterns = [
    path('baskets/', BasketViewSet.as_view({'get': 'list'})),

    path('baskets/add/', AddToBasketView.as_view(), name='add-to-cart'),
    path('baskets/basket-item/<int:item_id>/', UpdateBasketItemView.as_view(), name='update-cart-item'),
    path('payments/create/', CreatePaymentView.as_view(), name='create-payment'),
    path('webhooks/', webhook_view, name='webhook'),
    path('baskets/delete-items/', BasketItemDeleteView.as_view(), name='delete-basket-items'),
    # path('', include(router.urls)),


]
