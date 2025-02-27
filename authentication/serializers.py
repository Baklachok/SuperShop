import logging
from datetime import datetime
from django.contrib.auth import authenticate
from django.core import cache
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import TelNoCode
from supershop.settings import SIMPLE_JWT
from supershop.smser import send_verification_code
from supershop.telephone_check import isMobile
from .models import FrontendUser, UserRefreshToken

logger = logging.getLogger(__name__)  # Инициализация логгера

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=128, min_length=6, write_only=True)
    passwordConfirmation = serializers.CharField(write_only=True)

    class Meta:
        model = FrontendUser
        fields = ['telNo', 'name', 'password', 'passwordConfirmation']

    def validate(self, data):
        logger.info(f"Начало валидации регистрации для {data['telNo']}")
        if data['password'] != data['passwordConfirmation']:
            logger.warning("Пароли не совпадают")
            raise ValidationError({'password': "Passwords do not match.",
                                   'passwordConfirmation': "Passwords do not match."})

        parsed_number = isMobile(data['telNo'], None)
        if not parsed_number:
            logger.error(f"Неверный номер телефона: {data['telNo']}")
            raise ValidationError({'telNo': "Invalid phone number."})

        if FrontendUser.objects.filter(telNo=data['telNo']).exists():
            logger.warning(f"Пользователь с номером {data['telNo']} уже существует")
            raise ValidationError({'telNo': ['User with this telNo already exists.']})

        logger.info(f"Валидация прошла успешно для {data['telNo']}")
        return data

    def create(self, validated_data):
        validated_data.pop('passwordConfirmation')
        user = FrontendUser.objects.create_user(
            telNo=validated_data['telNo'],
            password=validated_data['password'],
            name=validated_data['name'],
            is_active=False,
        )
        logger.info(f"Создан пользователь {user.telNo}, но не активирован")
        return user


class MyTokenObtainSerializer(serializers.Serializer):
    telNo = serializers.CharField()
    password = serializers.CharField()
    code = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        telNo = attrs.get('telNo')
        code = attrs.get('code')
        password = attrs.get('password')

        if not telNo or not password:
            logger.warning("Отсутствует номер телефона или пароль")
            raise ValidationError({"error": "TelNo and password are required."})

        user = authenticate(username=telNo, password=password)
        if not user:
            logger.error(f"Не удалось аутентифицировать пользователя {telNo}")
            raise ValidationError({"telNo": "Invalid phone number."})

        if not user.is_active:
            logger.warning(f"Аккаунт {telNo} не активирован")
            if code:
                try:
                    stored_object = TelNoCode.objects.get(telNo=telNo)
                    if stored_object.code == code:
                        logger.info(f"Код {code} подтверждён для {telNo}")
                        user.is_active = True
                        user.is_phone_verified = True
                        user.save()
                        stored_object.delete()
                    else:
                        logger.error(f"Неверный код {code} для {telNo}")
                        raise ValidationError({"code": "Invalid code."})
                except TelNoCode.DoesNotExist:
                    logger.error(f"Код подтверждения не найден для {telNo}")
                    raise ValidationError({"code": "Code does not exist."})
            else:
                logger.info(f"Отправка кода подтверждения для {telNo}")
                send_verification_code(telNo)
                raise ValidationError({"code": "User account is disabled."})

        refresh = RefreshToken.for_user(user)
        UserRefreshToken.objects.create(
            user=user,
            token=str(refresh),
            expires_at=datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        )
        logger.info(f"Выдан токен для {telNo}")

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data


class ResetPasswordSerializer(serializers.Serializer):
    telNo = serializers.CharField()
    code = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        telNo = attrs.get('telNo')
        code = attrs.get('code')

        try:
            user = FrontendUser.objects.get(telNo=telNo)
        except FrontendUser.DoesNotExist:
            logger.error(f"Попытка сброса пароля для несуществующего номера {telNo}")
            raise ValidationError({"telNo": "User doesn't exist."})

        if user.is_active:
            if code:
                try:
                    stored_object = TelNoCode.objects.get(telNo=telNo)
                    if stored_object.code == code:
                        logger.info(f"Код {code} подтверждён для сброса пароля {telNo}")
                        stored_object.delete()
                    else:
                        logger.error(f"Неверный код {code} для {telNo}")
                        raise ValidationError({"code": "Invalid code."})
                except TelNoCode.DoesNotExist:
                    logger.error(f"Код подтверждения отсутствует для {telNo}")
                    raise ValidationError({"code": "Code does not exist."})

                refresh = RefreshToken.for_user(user)
                UserRefreshToken.objects.create(
                    user=user,
                    token=str(refresh),
                    expires_at=datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
                )
                logger.info(f"Выдан токен после сброса пароля для {telNo}")

                data['refresh'] = str(refresh)
                data['access'] = str(refresh.access_token)
                return data
            else:
                logger.info(f"Отправка кода подтверждения для сброса пароля {telNo}")
                send_verification_code(telNo)
                raise ValidationError({"code": "Haven't code"})
        else:
            logger.error(f"Попытка сброса пароля для неактивного аккаунта {telNo}")
            raise ValidationError({"code": "User account is disabled."})


class NewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    password_confirm = serializers.CharField()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            logger.warning("Пароли не совпадают при смене пароля")
            raise ValidationError({'password': "Passwords do not match.",
                                   'password_confirm': "Passwords do not match."})
        return data
