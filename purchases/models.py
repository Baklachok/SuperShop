import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy
from rest_framework.exceptions import ValidationError

from api.models import ItemStock
from authentication.models import FrontendUser


class Basket(models.Model):
    user = models.OneToOneField(FrontendUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Basket of {self.user}"

    @property
    def total_cost(self):
        return sum(item.total_price for item in self.items.all())

    # def __str__(self):
    #     return f"{self.item.item.name} - {self.item.color.name} - {self.item.size.name} ({self.quantity})"


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(ItemStock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)

    def __str__(self):
        return f"{self.product.item.name} in {self.basket}"

    @property
    def total_price(self):
        return self.product.item.price_with_discount * self.quantity

    def save(self, *args, **kwargs):
        # Check if the same product already exists in the basket
        existing_item = BasketItem.objects.filter(basket=self.basket, product=self.product).first()
        if existing_item and existing_item.pk != self.pk:
            # If it exists and is not the current item being saved, update the quantity
            existing_item.quantity += self.quantity
            existing_item.save()
            # Raise an exception to prevent the creation of a new BasketItem
            raise ValidationError(
                f"BasketItem with product '{self.product}' already exists. Quantity updated to {existing_item.quantity}.")
        super().save(*args, **kwargs)

class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', gettext_lazy('Pending')
        SUCCEEDED = 'SUCCEEDED', gettext_lazy('Succeeded')
        CANCELED = 'CANCELED', gettext_lazy('Canceled')
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name='payments')
    order_id = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    yookassa_payment_id = models.CharField(max_length=100, blank=True, null=True)
    yookassa_confirmation_url = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.order_id