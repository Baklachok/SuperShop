from django.db import models

from api.models import ItemStock
from authentication.models import FrontendUser


class Basket(models.Model):
    user = models.OneToOneField(FrontendUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user}"

    @property
    def total_cost(self):
        return sum(item.total_price for item in self.items.all())

    # def __str__(self):
    #     return f"{self.item.item.name} - {self.item.color.name} - {self.item.size.name} ({self.quantity})"


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(ItemStock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.item.name} in {self.basket}"

    @property
    def total_price(self):
        return self.product.item.price * self.quantity
