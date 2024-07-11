from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from autoslug import AutoSlugField
from unidecode import unidecode


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from='get_slug', unique=True, always_update=True, default='temp-slug')
    photo = models.ImageField(upload_to='categories/', blank=True)

    def get_slug(self):
        return unidecode(self.name)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    categories = models.ManyToManyField(Category, related_name='items')
    rating = models.DecimalField(max_digits=2, decimal_places=1,validators=[MinValueValidator(0), MaxValueValidator(5)], default=0)
    order_count = models.PositiveIntegerField(default=0)
    discount = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(1)], default=0)
    price_with_discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0, editable=False)
    # general_photo = models.ForeignKey(Item_Photos, related_name='items', limit_choices_to={'is_gen': True})

    def save(self, *args, **kwargs):
        self.price_with_discount = self.price * (1 - self.discount)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
