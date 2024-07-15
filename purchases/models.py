from django.db import models

from api.models import ItemStock
from authentication.models import FrontendUser

class Basket(models.Model):
    user = models.ForeignKey(FrontendUser, on_delete=models.CASCADE, related_name='baskets')

    def __str__(self):
        return f"Cart of {self.user}"

class BasketItem(models.Model):
    item = models.ForeignKey(ItemStock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    basket = models.ForeignKey(Basket, related_name='baskets', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.item.item.name} - {self.item.color.name} - {self.item.size.name} ({self.quantity})"
