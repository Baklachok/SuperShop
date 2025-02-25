import logging
from rest_framework import serializers

from authentication.models import FrontendUser
from orders.models import Order
from .models import Basket, BasketItem, Payment, Favourites, FavouritesItem
from yookassa import Payment as YooKassaPayment


logger = logging.getLogger(__name__)

class BasketItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.item.name', read_only=True)
    product_price = serializers.DecimalField(source='product.item.price', max_digits=10, decimal_places=2,
                                             read_only=True)
    item_id = serializers.CharField(source='product.item.id', read_only=True)
    color = serializers.CharField(source='product.color', read_only=True)
    size = serializers.CharField(source='product.size', read_only=True)
    product_price_with_discount = serializers.CharField(source='product.item.price_with_discount', read_only=True)
    product_image = serializers.ImageField(source='product.item.general_photo_one.photo.photo', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    category_slug = serializers.SerializerMethodField()
    max_quantity = serializers.IntegerField(source='product.quantity', read_only=True)

    class Meta:
        model = BasketItem
        fields = ['id', 'product', 'product_name', 'item_id', 'category_slug', 'product_price',
                  'product_price_with_discount',
                  'product_image', 'color', 'size', 'quantity', 'total_price', 'in_stock', 'max_quantity']

    def get_category_slug(self, obj):
        categories = obj.product.item.categories.all()
        return [category.slug for category in categories]


class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_available_to_order = serializers.BooleanField(read_only=True)
    without_discount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Basket
        fields = ['id', 'user', 'items', 'total_cost', 'is_available_to_order', 'without_discount', 'created_at',
                  'updated_at']


class AddToBasketSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    color = serializers.CharField()
    size = serializers.CharField()
    quantity = serializers.IntegerField()

    class Meta:
        fields = ['item_id', 'color', 'size', 'quantity']


class BasketItemDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )


class FavouritesItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.item.name', read_only=True)
    product_price = serializers.DecimalField(source='product.item.price', max_digits=10, decimal_places=2,
                                             read_only=True)
    item_id = serializers.IntegerField(source='product.item.id', read_only=True)
    product_price_with_discount = serializers.DecimalField(source='product.item.price_with_discount', max_digits=10,
                                                           decimal_places=2, read_only=True)
    product_image_1 = serializers.ImageField(source='product.item.general_photo_one.photo.photo', read_only=True)
    product_image_2 = serializers.ImageField(source='product.item.general_photo_two.photo.photo', read_only=True)
    category_slug = serializers.SerializerMethodField()

    class Meta:
        model = FavouritesItem
        fields = ['id', 'product', 'product_name', 'item_id', 'category_slug', 'product_price',
                  'product_price_with_discount', 'product_image_1', 'product_image_2']

    def get_category_slug(self, obj):
        categories = obj.product.item.categories.all()
        return [category.slug for category in categories]


class FavouritesSerializer(serializers.ModelSerializer):
    items = FavouritesItemSerializer(many=True, read_only=True)

    class Meta:
        model = Favourites
        fields = ['id', 'items', 'created_at', 'updated_at']


class CreatePaymentSerializer(serializers.Serializer):
    basket_id = serializers.PrimaryKeyRelatedField(queryset=Basket.objects.all())
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def create(self, validated_data):
        basket = validated_data["basket_id"]
        user = self.context["request"].user

        logger.info(
            "Создание платежа: пользователь=%s, корзина_id=%s, сумма=%s",
            user, basket.id, validated_data["amount"]
        )

        try:
            payment = Payment.objects.create(
                user=user,
                basket=basket,
                amount=validated_data["amount"],
                status="created",
            )
            logger.info("Платеж успешно создан: %s", payment)
        except Exception as e:
            logger.error("Ошибка при создании платежа: %s", e)
            raise

        return payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'basket', 'amount', 'status', 'yookassa_payment_id',
                  'yookassa_confirmation_url',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'yookassa_payment_id', 'yookassa_confirmation_url', 'created_at',
                            'updated_at']
