# backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import AdminUser, FrontendUser


class AdminBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = AdminUser.objects.get(email=username)
            if user.check_password(password):
                return user
        except AdminUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return AdminUser.objects.get(pk=user_id)
        except AdminUser.DoesNotExist:
            return None


class FrontendBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = FrontendUser.objects.get(telNo=username)
            if user.check_password(password):
                return user
        except FrontendUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return FrontendUser.objects.get(pk=user_id)
        except FrontendUser.DoesNotExist:
            return None
