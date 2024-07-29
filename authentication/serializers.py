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


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=6,
        write_only=True
    )
    passwordConfirmation = serializers.CharField(write_only=True)

    class Meta:
        model = FrontendUser
        # Перечислить все поля, которые могут быть включены в запрос
        # или ответ, включая поля, явно указанные выше.
        fields = ['telNo', 'name', 'password', 'passwordConfirmation']

    def validate(self, data):
        if data['password'] != data['passwordConfirmation']:
            raise ValidationError({'password': "Passwords do not match.",
                                   'passwordConfirmation': "Passwords do not match."})
        parsed_number = isMobile(data['telNo'], None)
        if not parsed_number:
            raise ValidationError({'telNo': "Invalid phone number."})
        if FrontendUser.objects.filter(telNo=data['telNo']).exists():
            raise ValidationError({'telNo': ['user with this telNo already exists.']})
        return data

    def create(self, validated_data):
        validated_data.pop('passwordConfirmation')
        user = FrontendUser.objects.create_user(
            telNo=validated_data['telNo'],
            password=validated_data['password'],
            name=validated_data['name'],
            is_active=False,
        )
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
        if not telNo:
            raise ValidationError({"telNo": "Must include 'telNo'."})
        if not password:
            raise ValidationError({"password": "Must include 'password'."})
        user = authenticate(username=telNo, password=password)
        if not user:
            raise ValidationError({"telNo": "Invalid phone number."})
        if not user.is_active:
            print('user account is disabled')
            if code:
                print('code est')
                stored_object = TelNoCode.objects.get(telNo=telNo)
                stored_code = stored_object.code
                print(stored_code)
                print(code)
                if stored_code == code:
                    print('code match')
                    user.is_active = True
                    user.is_phone_verified = True
                    user.save()
                    stored_object.delete()
                    print("Ваш номер подтвержден!")
                else:
                    print("Неверный код.")
            else:
                print('nachali otpravku')
                send_verification_code(telNo)
                print('zakonchili otpravku')
                raise ValidationError({"code": "User account is disabled."})
        refresh = RefreshToken.for_user(user)
        UserRefreshToken.objects.create(
            user=user,
            token=str(refresh),
            expires_at=datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        )
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
            raise ValidationError({"telNo": "User doesn't exist."})

        if user.is_active:
            if code:
                print('code est')
                try:
                    stored_object = TelNoCode.objects.get(telNo=telNo)
                    stored_code = stored_object.code
                except TelNoCode.DoesNotExist:
                    raise ValidationError({"code": "error"})
                print(stored_code)
                print(code)
                if stored_code == code:
                    print('code match')
                    print("mpzhno perehodit k novomu!")
                    stored_object.delete()
                else:
                    print("Неверный код.")
                    raise ValidationError({"code": "doesnt match"})
                refresh = RefreshToken.for_user(user)
                UserRefreshToken.objects.create(
                    user=user,
                    token=str(refresh),
                    expires_at=datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

                )
                data['refresh'] = str(refresh)
                data['access'] = str(refresh.access_token)
                return data
            else:
                print('nachali otpravku')
                send_verification_code(telNo)
                print('zakonchili otpravku')
                raise ValidationError({"code": "Haven't code"})
        else:
            raise ValidationError({"code": "User account is disabled."})



class NewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    password_confirm = serializers.CharField()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise ValidationError({'password': "Passwords do not match.",
                                   'password_confirm': "Passwords do not match."})
        return data