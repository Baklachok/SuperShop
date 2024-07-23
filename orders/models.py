from django.db import models

from api.models import ItemStock
from authentication.models import FrontendUser


class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('paid', 'Оплачен'),
        ('delivered', 'Доставлен'),
        ('received', 'Получен'),
        ('canceled', 'Отменен'),
    ]

    user = models.ForeignKey(FrontendUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')

    def __str__(self):
        return f"Order {self.id} by {self.user}"

    def total_cost(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(ItemStock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.item.name} in Order {self.order.id}"

    @property
    def total_price(self):
        return self.product.item.price_with_discount * self.quantity

    def update_order_status(self, new_status):
        self.status = new_status
        self.save()
