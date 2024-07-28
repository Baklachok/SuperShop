from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.item.name')
    item_photo = serializers.ImageField(source='product.item.general_photo_one.photo.photo')
    item_id = serializers.ReadOnlyField(source='product.item.id')
    total_price = serializers.ReadOnlyField()
    category_slug = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'item_photo', 'item_id', 'category_slug', 'product_name', 'quantity',
                  'total_price']
        read_only_fields = ['id', 'order', 'total_price']

    def get_category_slug(self, obj):
        categories = obj.product.item.categories.all()
        return [category.slug for category in categories]



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'payment', 'created_at', 'updated_at', 'status', 'items', 'total_cost']
        read_only_fields = ['id', 'created_at', 'updated_at', 'items', 'total_cost']
