from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, name, telNo, password=None, **extra_fields):
        if not telNo:
            raise ValueError('The telNo field must be set')
        user = self.model(name=name, telNo=telNo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telNo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(telNo, password, **extra_fields)


class MyUser(AbstractUser):
    name = models.CharField(max_length=100)
    telNo = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    objects = CustomUserManager()


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.name
