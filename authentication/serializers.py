from datetime import datetime


from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from supershop.settings import SIMPLE_JWT
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
        )
        return user


class MyTokenObtainSerializer(serializers.Serializer):
    telNo = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        data = super().validate(attrs)
        telNo = attrs.get('telNo')
        password = attrs.get('password')
        if not telNo:
            raise ValidationError({"telNo": "Must include 'telNo'."})
        if not password:
            raise ValidationError({"password": "Must include 'password'."})
        user = authenticate(username=telNo, password=password)
        if not user:
            raise ValidationError({"telNo": "Invalid phone number."})
        refresh = RefreshToken.for_user(user)
        UserRefreshToken.objects.create(
            user=user,
            token=str(refresh),
            expires_at=datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        )
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data

