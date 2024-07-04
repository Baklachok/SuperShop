from rest_framework import serializers
from .models import Item, MyUser
from django.contrib.auth import get_user_model


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    passwordConfirmation = serializers.CharField(write_only=True)

    class Meta:
        model = MyUser
        fields = ('name', 'telNo', 'password', 'passwordConfirmation')

    def validate(self, data):
        if data['password'] != data['passwordConfirmation']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('passwordConfirmation')
        user = User.objects.create_user(
            username=validated_data['name'],
            telNo=validated_data['telNo'],
            password=validated_data['password']
        )
        return user
