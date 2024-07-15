# backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from rest_framework import exceptions
from rest_framework.authentication import get_authorization_header
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

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

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != b'bearer':
            # Если нет заголовка Authorization, проверяем куки
            raw_token = request.COOKIES.get("access_token")
        else:
            if len(header) == 1:
                raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
            elif len(header) > 2:
                raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

            raw_token = header[1].decode('utf-8')

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user_id = validated_token.get('user_id')
        user = FrontendUser.objects.get(pk=user_id)
        return user, validated_token

    def get_validated_token(self, raw_token):
        try:
            return super().get_validated_token(raw_token)
        except InvalidToken as e:
            raise exceptions.AuthenticationFailed(str(e))