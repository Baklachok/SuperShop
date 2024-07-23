from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.item.name')
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_name', 'quantity', 'total_price']
        read_only_fields = ['id', 'order', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'payment', 'created_at', 'updated_at', 'status', 'items', 'total_cost']
        read_only_fields = ['id', 'created_at', 'updated_at', 'items', 'total_cost']
