from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# class MyUser(AbstractUser):
#     groups = models.ManyToManyField(
#         Group,
#         related_name='myuser_set',  # Измените related_name
#         blank=True,
#         help_text='The groups this user belongs to.',
#         verbose_name='groups'
#     )
#     user_permissions = models.ManyToManyField(
#         Permission,
#         related_name='myuser_set',  # Измените related_name
#         blank=True,
#         help_text='Specific permissions for this user.',
#         verbose_name='user permissions'
#     )
#     name = models.CharField(max_length=100)
#     telNo = models.CharField(max_length=100)
#     password = models.CharField(max_length=100)
#     passwordConfirmation = models.CharField(max_length=100)

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    category = models.CharField(max_length=100, null=True)
    #category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], default=0)
    order_count = models.PositiveIntegerField(default=0)
    discount = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(1)], default=0)
    price_with_discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0, editable=False)
    # general_photo = models.ForeignKey(Item_Photos, related_name='items', limit_choices_to={'is_gen': True})

    def save(self, *args, **kwargs):
        self.price_with_discount = self.price * (1 - self.discount)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
