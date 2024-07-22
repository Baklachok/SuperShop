from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Item, ItemStock, Color, Size
from authentication.backends import CookieJWTAuthentication
from .models import Basket, BasketItem, Favourites, FavouritesItem
from .serializers import BasketSerializer, BasketItemSerializer, AddToBasketSerializer, FavouritesSerializer, \
    BasketItemDeleteSerializer


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


class BasketItemDeleteView(APIView):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        serializer = BasketItemDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        product_ids = serializer.validated_data['ids']

        if not product_ids:
            return Response({"error": True, "message": "Product IDs are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            basket_items = BasketItem.objects.filter(id__in=product_ids)
            if not basket_items.exists():
                return Response({"error": True, "message": "No matching items found to delete"},
                                status=status.HTTP_404_NOT_FOUND)

            basket_items.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except BasketItem.DoesNotExist:
            return Response({"error": True, "message": "Some basket items do not exist"},
                            status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": True, "message": "Invalid product IDs"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddToBasketView(generics.CreateAPIView):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]
    serializer_class = AddToBasketSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            item_id = serializer.validated_data['item_id']
            color = serializer.validated_data['color']
            size = serializer.validated_data['size']
            quantity = serializer.validated_data['quantity']
            color_id = Color.objects.get(name=color).id
            size_id = Size.objects.get(name=size).id

            try:
                product = ItemStock.objects.get(item=item_id, color=color_id, size=size_id)
            except ItemStock.DoesNotExist:
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

#
# class FavouritesViewSet(viewsets.ModelViewSet):
#     authentication_classes = [CookieJWTAuthentication, ]
#     permission_classes = [IsAuthenticated]
#     queryset = Favourites.objects.all()
#     serializer_class = FavouritesSerializer
#
#     @action(detail=True, methods=['post'], url_path='add_item')
#     def add_item(self, request, pk=None):
#         print('ya zashel')
#         favourites = Favourites.objects.get(user=request.user)
#         product_id = pk
#         try:
#             product = ItemStock.objects.get(id=product_id)
#         except Item.DoesNotExist:
#             return Response({"error": True, "message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         if FavouritesItem.objects.filter(favourites=favourites, product=product).exists():
#             return Response({'error': True, 'message': 'Product already in favourites'}, status=status.HTTP_400_BAD_REQUEST)
#
#         FavouritesItem.objects.create(favourites=favourites, product=product)
#         return Response({'success': True, 'message': 'Product added to favourites'}, status=status.HTTP_201_CREATED)
#
#     @action(detail=True, methods=['post'])
#     def remove_item(self, request, pk=None):
#         favourites = Favourites.objects.get(user=request.user)
#         product_id = pk
#
#         favourite_item = FavouritesItem.objects.filter(favourites=favourites, product=product).first()
#         if favourite_item:
#             favourite_item.delete()
#             return Response({'success': True, 'message': 'Product removed from favourites'}, status=status.HTTP_204_NO_CONTENT)
#
#         return Response({'error': True, 'message': 'Product not in favourites'}, status=status.HTTP_400_BAD_REQUEST)
