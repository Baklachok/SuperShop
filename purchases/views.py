import json
import logging

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

logger = logging.getLogger(__name__)

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
        logger.info(f"Пользователь {user} пытается обновить товар {item_id} в корзине.")

        quantity = request.data.get('quantity')
        if quantity is None:
            logger.warning(f"Пользователь {user} не передал quantity.")
            return Response({"error": True, "message": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                logger.warning(f"Пользователь {user} указал некорректное количество ({quantity}).")
                return Response({"error": True, "message": "Quantity must be a positive integer"},
                                status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            logger.error(f"Пользователь {user} передал некорректное значение quantity: {quantity}")
            return Response({"error": True, "message": "Quantity must be an integer"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            basket = Basket.objects.get(user=user)
        except Basket.DoesNotExist:
            logger.error(f"Корзина пользователя {user} не найдена.")
            return Response({"error": True, "message": "Basket not exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            basket_item = BasketItem.objects.get(basket=basket.id, pk=item_id)
        except BasketItem.DoesNotExist:
            logger.error(f"Товар {item_id} в корзине пользователя {user} не найден.")
            return Response({"error": True, "message": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        basket_item.quantity = quantity
        basket_item.save()
        logger.info(f"Пользователь {user} обновил товар {item_id} в корзине до {quantity} шт.")

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
        logger.info(f"Поступил запрос {request.method} на {request.path}. Данные запроса: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            item_id = serializer.validated_data['item_id']
            color = serializer.validated_data['color']
            size = serializer.validated_data['size']
            quantity = serializer.validated_data['quantity']

            logger.info(f"Полученные данные: item_id={item_id}, color={color}, size={size}, quantity={quantity}")

            try:
                logger.info(f"Пытаемся найти объект Color с именем '{color}'")
                color_obj = Color.objects.get(name=color)
                color_id = color_obj.id
                logger.info(f"Найден Color: {color_obj} (id={color_id})")
            except Color.DoesNotExist:
                logger.warning(f"Цвет '{color}' не найден в базе.")
                return Response({"error": True, "message": "Invalid color"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                logger.info(f"Пытаемся найти объект Size с именем '{size}'")
                size_obj = Size.objects.get(name=size)
                size_id = size_obj.id
                logger.info(f"Найден Size: {size_obj} (id={size_id})")
            except Size.DoesNotExist:
                logger.warning(f"Размер '{size}' не найден в базе.")
                return Response({"error": True, "message": "Invalid size"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Логирование всех записей для товара item_id
                existing_stock = ItemStock.objects.all().values("id", "item", "color", "size")
                logger.info(f"Все записи ItemStock: {list(existing_stock)}")
                
                logger.info(f"Пытаемся найти товар с item_id={item_id}, color_id={color_id}, size_id={size_id}")
                product = ItemStock.objects.get(item=item_id, color=color_id, size=size_id)
                logger.info(f"Товар найден: {product}")
            except ItemStock.DoesNotExist:
                logger.error(f"Товар item_id={item_id}, color={color}, size={size} не найден.")
                return Response({"error": True, "message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            logger.info("Пытаемся получить или создать корзину для пользователя.")
            basket, basket_created = Basket.objects.get_or_create(user=user)
            if basket_created:
                logger.info(f"Создана новая корзина для пользователя {user}.")
            else:
                logger.info(f"Найдена существующая корзина для пользователя {user}.")

            logger.info("Пытаемся получить или создать элемент корзины для найденного товара.")
            basket_item, item_created = BasketItem.objects.get_or_create(basket=basket, product=product)
            if not item_created:
                basket_item.quantity += quantity
                logger.info(f"Количество товара обновлено: {basket_item.quantity} шт.")
            else:
                basket_item.quantity = quantity
                logger.info(f"Товар добавлен в корзину: {basket_item.quantity} шт.")

            basket_item.save()

            basket_item_serializer = BasketItemSerializer(basket_item)
            logger.info(f"Товар успешно добавлен/обновлён в корзине. Ответ: {basket_item_serializer.data}")

            return Response(basket_item_serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(f"Ошибка валидации данных: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreatePaymentView(CreateAPIView):
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [IsAuthenticated]
    serializer_class = CreatePaymentSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        logger.info(f"Пользователь {user} пытается создать платеж.")

        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        basket_id = serializer.validated_data['basket_id']
        try:
            basket = Basket.objects.get(id=basket_id.id, user=user)
        except Basket.DoesNotExist:
            logger.error(f"Корзина {basket_id} не найдена или не принадлежит пользователю {user}.")
            return Response({"detail": "Basket not found or does not belong to this user."},
                            status=status.HTTP_404_NOT_FOUND)

        amount = basket.total_cost
        logger.info(f"Создаётся платёж для корзины {basket.id} на сумму {amount} RUB.")

        payment = Payment.objects.create(basket=basket, amount=amount, user=user)
        payment_request = {
            "amount": {"value": str(amount), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "http://127.0.0.1:3000/cart"},
            "capture": True,
            "description": f"Payment for basket {basket.id}"
        }

        try:
            yoo_payment = YooKassaPayment.create(payment_request)
            payment.yookassa_payment_id = yoo_payment.id
            payment.yookassa_confirmation_url = yoo_payment.confirmation.confirmation_url
            payment.save()
            logger.info(f"Платёж {payment.id} успешно создан. YooKassa ID: {yoo_payment.id}")
        except Exception as e:
            logger.error(f"Ошибка при создании платежа в YooKassa: {e}")
            return Response({"error": True, "message": "Ошибка при создании платежа"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order = Order.objects.create(user=user, status='created', payment=payment)
        basket_items = BasketItem.objects.filter(basket=basket)
        for item in basket_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)

        logger.info(f"Заказ {order.id} создан для пользователя {user}.")
        payment_serializer = PaymentSerializer(payment)
        return Response(payment_serializer.data, status=status.HTTP_201_CREATED)



@csrf_exempt
def webhook_view(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            logger.info(f"Получен вебхук: {payload}")

            payment_id = payload['object']['id']
            status = payload['object']['status']
            
            logger.info(f"Обновляем платёж {payment_id} со статусом {status}.")

            try:
                payment = Payment.objects.get(yookassa_payment_id=payment_id)
                payment.status = status.upper()

                if payment.status == Payment.PaymentStatus.SUCCEEDED:
                    logger.info(f"Платёж {payment_id} подтверждён. Обновляем заказ и уменьшаем количество на складе.")

                    basket_items = BasketItem.objects.filter(basket=payment.basket)
                    order = Order.objects.get(user=payment.user, payment=payment)
                    order.status = "paid"
                    order.save()

                    for item in basket_items:
                        stock_item = ItemStock.objects.get(item=item.product.item, color=item.product.color, size=item.product.size)
                        stock_item.quantity -= item.quantity
                        stock_item.save()
                        item.product.item.order_count += item.quantity
                        item.product.item.save()

                    basket_items.delete()
                    logger.info(f"Заказ {order.id} успешно завершён и оплачен.")

                payment.save()
                return JsonResponse({'success': True}, status=200)

            except Payment.DoesNotExist:
                logger.error(f"Платёж {payment_id} не найден в системе.")
                return JsonResponse({'error': True, 'message': 'Payment not found'}, status=404)

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при обработке JSON вебхука: {e}")
            return JsonResponse({'error': True, 'message': 'Invalid JSON'}, status=400)

    else:
        logger.warning("Попытка обращения к вебхуку не через POST.")
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
        logger.info("Начало создания платежа. Данные запроса: %s", request.data)
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error("Ошибка валидации платежа: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment = serializer.save()
        logger.info("Платеж успешно создан: %s", payment)

        headers = self.get_success_headers(serializer.data)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED, headers=headers)