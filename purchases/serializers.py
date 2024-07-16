from rest_framework import serializers
from .models import Basket, BasketItem


class BasketItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.item.name', read_only=True)
    product_price = serializers.DecimalField(source='product.item.price', max_digits=10, decimal_places=2,
                                             read_only=True)
    item_id = serializers.CharField(source='product.item.id', read_only=True)
    product_price_with_discount = serializers.CharField(source='product.item.price_with_discount', read_only=True)
    product_image = serializers.ImageField(source='product.item.general_photo_one.photo.photo', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    category_slug = serializers.SerializerMethodField()

    class Meta:
        model = BasketItem
        fields = ['id', 'product', 'product_name', 'item_id', 'category_slug', 'product_price',
                  'product_price_with_discount',
                  'product_image', 'quantity', 'total_price']

    def get_category_slug(self, obj):
        categories = obj.product.item.categories.all()
        return [category.slug for category in categories]


class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Basket
        fields = ['id', 'user', 'items', 'total_cost', 'created_at', 'updated_at']


class AddToBasketSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    class Meta:
        fields = ['product_id', 'quantity']
    # def create(self, validated_data):
    #     items_data = validated_data.pop('items')
    #     basket = Basket.objects.create(**validated_data)
    #     for item_data in items_data:
    #         BasketItem.objects.create(basket=basket, **item_data)
    #     return basket
    #
    # def update(self, instance, validated_data):
    #     items_data = validated_data.pop('items')
    #     instance.user = validated_data.get('user', instance.user)
    #     instance.save()
    #
    #     for item_data in items_data:
    #         item = item_data.get('item')
    #         quantity = item_data.get('quantity')
    #         basket_item, created = BasketItem.objects.get_or_create(basket=instance, item=item)
    #         if not created:
    #             basket_item.quantity = quantity
    #             basket_item.save()
    #
    #     return instance
