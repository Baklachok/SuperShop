import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, generics
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Item, ItemStock
from authentication.backends import CookieJWTAuthentication
from .models import Basket, BasketItem, Payment
from .serializers import BasketSerializer, BasketItemSerializer, AddToBasketSerializer, PaymentSerializer, \
    CreatePaymentSerializer

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

        # Создаем платеж и возвращаем ответ
        payment = serializer.save()
        payment_serializer = PaymentSerializer(payment)
        return Response(payment_serializer.data, status=status.HTTP_201_CREATED)

class UpdatePaymentStatusView(APIView):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        payment_id = request.data.get('payment_id')
        if not payment_id:
            return Response({"error": True, "message": "Payment ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"error": True, "message": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            yoo_payment = YooKassaPayment.find_one(payment.yookassa_payment_id)
        except Exception as e:
            return Response({"error": True, "message": f"Error fetching payment from YooKassa: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment.status = yoo_payment.status
        payment.save()

        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)


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

            # Find the corresponding Payment object
            try:
                payment = Payment.objects.get(yookassa_payment_id=payment_id)
                payment.status = status.upper()  # Assuming your PaymentStatus choices are in uppercase

                if payment.status == Payment.PaymentStatus.SUCCEEDED:
                    basket_items = BasketItem.objects.filter(basket=payment.basket)

                    # Update stock quantities
                    for item in basket_items:
                        stock_item = ItemStock.objects.get(item=item.product.item, color=item.product.color, size=item.product.size)
                        stock_item.quantity -= item.quantity
                        stock_item.save()

                    # Clear the basket
                    basket_items.delete()

                payment.save()
                return JsonResponse({'status': 'success'}, status=200)
            except Payment.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
