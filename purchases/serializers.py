from rest_framework import serializers
from .models import Basket, BasketItem


class BasketItemSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.item.name')

    class Meta:
        model = BasketItem
        fields = ['item', 'quantity', "item_name"]


class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True)
    print(items)

    class Meta:
        model = Basket
        fields = ['user', 'items']

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
