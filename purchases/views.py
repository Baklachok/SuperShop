import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, generics
from rest_framework.generics import CreateAPIView
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Item, ItemStock, Color, Size
from authentication.backends import CookieJWTAuthentication
from orders.models import Order, OrderItem

from .models import Basket, BasketItem, Payment, Favourites, FavouritesItem
from .serializers import BasketSerializer, BasketItemSerializer, AddToBasketSerializer, PaymentSerializer, \
    CreatePaymentSerializer, FavouritesSerializer, \
    BasketItemDeleteSerializer

from yookassa import Payment as YooKassaPayment


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


class CreatePaymentView(CreateAPIView):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]
    serializer_class = CreatePaymentSerializer

    def post(self, request, *args, **kwargs):

        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Получаем данные из валидированного сериализатора
        basket_id = serializer.validated_data['basket_id']
        user = request.user
        try:
            basket = Basket.objects.get(id=basket_id.id, user=user)
        except Basket.DoesNotExist:
            return Response({"detail": "Basket not found or does not belong to this user."},
                            status=status.HTTP_404_NOT_FOUND)

        amount = basket.total_cost
        payment = Payment.objects.create(basket=basket, amount=amount, user=user)
        # Создание платежа через YooKassa
        payment_request = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "http://127.0.0.1:3000/cart"
            },
            "capture": True,
            "description": f"Payment for basket {basket.id}"
        }
        yoo_payment = YooKassaPayment.create(payment_request)
        payment.yookassa_payment_id = yoo_payment.id
        payment.yookassa_confirmation_url = yoo_payment.confirmation.confirmation_url
        # Создаем платеж и возвращаем ответ
        payment.save()
        order = Order.objects.create(user=user, status='created', payment=payment)
        basket_items = BasketItem.objects.filter(basket=basket)
        for item in basket_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )
        payment_serializer = PaymentSerializer(payment)
        return Response(payment_serializer.data, status=status.HTTP_201_CREATED)


@csrf_exempt
def webhook_view(request):
    if request.method == 'POST':
        try:
            # Parse JSON payload
            payload = json.loads(request.body)

            # Process webhook data here
            print("Received webhook data:", payload)

            # Get payment ID from webhook
            payment_id = payload['object']['id']
            status = payload['object']['status']
            print(payload)
            # Find the corresponding Payment object
            try:
                payment = Payment.objects.get(yookassa_payment_id=payment_id)
                payment.status = status.upper()  # Assuming your PaymentStatus choices are in uppercase

                if payment.status == Payment.PaymentStatus.SUCCEEDED:
                    basket_items = BasketItem.objects.filter(basket=payment.basket)
                    order = Order.objects.get(user=payment.user, payment=payment)
                    order.status = "paid"
                    order.save()

                    # Update stock quantities
                    for item in basket_items:
                        stock_item = ItemStock.objects.get(item=item.product.item, color=item.product.color,
                                                           size=item.product.size)
                        stock_item.quantity -= item.quantity
                        stock_item.save()

                        item.product.item.order_count += item.quantity
                        item.product.item.save()

                    # Clear the basket
                    basket_items.delete()

                payment.save()
                return JsonResponse({'success': True}, status=200)
            except Payment.DoesNotExist:
                return JsonResponse({'error': True, 'message': 'Payment not found'}, status=404)

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            return JsonResponse({'error': True, 'message': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': True, 'message': 'Invalid method'}, status=405)


class FavouritesViewSet(viewsets.ModelViewSet):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Favourites.objects.all()
    serializer_class = FavouritesSerializer

    def get_queryset(self):
        # Ensure users can only access their own favourites
        return Favourites.objects.filter(user=self.request.user)

    # def create(self, request, *args, **kwargs):
    #     # Check if the user already has a Favourites object
    #     favourites, created = Favourites.objects.get_or_create(user=request.user)
    #     serializer = self.get_serializer(favourites)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='add_item')
    def add_item(self, request):
        print(request.user)
        product_id = request.data.get('product_id')
        try:
            product = ItemStock.objects.get(id=product_id)
        except ItemStock.DoesNotExist:
            return Response({"error": True, "message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        favourites, created = Favourites.objects.get_or_create(user=request.user)
        print(favourites)
        if FavouritesItem.objects.filter(favourites=favourites, product=product).exists():
            return Response({'error': True, 'message': 'Product already in favourites'},
                            status=status.HTTP_400_BAD_REQUEST)

        FavouritesItem.objects.create(favourites=favourites, product=product)
        return Response({'success': True, 'message': 'Product added to favourites'}, status=status.HTTP_201_CREATED)


class PaymentsViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePaymentSerializer
        return PaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED, headers=headers)
