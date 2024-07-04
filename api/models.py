from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator
from django.db import models

class MyUser(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name='myuser_set',  # Измените related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='myuser_set',  # Измените related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    name = models.CharField(max_length=100)
    telNo = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    passwordConfirmation = models.CharField(max_length=100)

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.name
