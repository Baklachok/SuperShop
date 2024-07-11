# models.py


import jwt
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import datetime

from supershop import settings


class AdminUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        return self.create_user(email, password, **extra_fields)


class FrontendUserManager(BaseUserManager):
    def create_user(self, telNo, password=None, **extra_fields):
        if not telNo:
            raise ValueError('The telNo field must be set')
        user = self.model(telNo=telNo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class AdminUser(AbstractBaseUser, PermissionsMixin):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='adminuser_set',
        blank=True,
        help_text='The groups this admin belongs to. An admin will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='adminuser_set',
        blank=True,
        help_text='Specific permissions for this admin.',
        verbose_name='user permissions'
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    objects = AdminUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class FrontendUser(AbstractBaseUser, PermissionsMixin):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_set_custom',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_set_custom',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    # прочитать про поле
    profile_picture = models.ImageField(upload_to='profile_pictures',default="default.png")
    name = models.CharField(max_length=100, blank=False, null=True)
    # my_orders
    # my_favourites
    # my_comments
    # my_addresses
    telNo = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    objects = FrontendUserManager()

    USERNAME_FIELD = 'telNo'
    REQUIRED_FIELDS = []

    def __str__(self):
        """ Строковое представление модели (отображается в консоли) """
        return self.telNo


