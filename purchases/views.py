from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Item, ItemStock
from authentication.backends import CookieJWTAuthentication
from .models import Basket, BasketItem
from .serializers import BasketSerializer, BasketItemSerializer, AddToBasketSerializer


class BasketViewSet(viewsets.ModelViewSet):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]
    serializer_class = BasketSerializer

    def get_queryset(self):
        return Basket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UpdateBasketItemView(APIView):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        user = request.user
        quantity = request.data.get('quantity')

        if quantity is None:
            return Response({"error": True, "message": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"error": True, "message": "Quantity must be a positive integer"},
                                status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": True, "message": "Quantity must be an integer"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            basket = Basket.objects.get(user=user)
        except Basket.DoesNotExist:
            return Response({"error": True, "message": "Basket not exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            basket_item = BasketItem.objects.get(basket=basket.id, pk=item_id)
        except BasketItem.DoesNotExist:
            return Response({"error": True, "message": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        basket_item.quantity = quantity
        basket_item.save()

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddToBasketView(generics.CreateAPIView):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]
    serializer_class = AddToBasketSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']

            try:
                product = ItemStock.objects.get(id=product_id)
            except Item.DoesNotExist:
                return Response({"error": True, "message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            basket, created = Basket.objects.get_or_create(user=user)
            basket_item, created = BasketItem.objects.get_or_create(basket=basket, product=product)

            if not created:
                basket_item.quantity += quantity
            else:
                basket_item.quantity = quantity
            basket_item.save()

            basket_item_serializer = BasketItemSerializer(basket_item)
            return Response(basket_item_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
