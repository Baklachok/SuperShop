from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import FrontendUser


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
            raise serializers.ValidationError("Passwords do not match.")
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
        if telNo and password:
            user = authenticate(username=telNo, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                data['refresh'] = str(refresh)
                data['access'] = str(refresh.access_token)
                return data
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password")
        return data
