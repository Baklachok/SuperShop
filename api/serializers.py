from rest_framework import serializers

from .models import Item, Category
from django.contrib.auth import get_user_model

class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='category-detail', lookup_field='slug')
    items_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'


    def get_items_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/api/categories/{obj.slug}/items/')

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


# User = get_user_model()
#
#
# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
#     passwordConfirmation = serializers.CharField(write_only=True)
#
#     class Meta:
#         model = MyUser
#         fields = ('name', 'telNo', 'password', 'passwordConfirmation')
#
#     def validate(self, data):
#         if data['password'] != data['passwordConfirmation']:
#             raise serializers.ValidationError("Passwords do not match.")
#         return data
#
#     def create(self, validated_data):
#         validated_data.pop('passwordConfirmation')
#         user = User.objects.create_user(

#             name=validated_data['name'],

#             telNo=validated_data['telNo'],
#             password=validated_data['password']
#         )
#         return user
