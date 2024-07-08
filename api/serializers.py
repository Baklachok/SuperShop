from rest_framework import serializers

from .models import Item, Category, Photo, Item_Photos
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

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = '__all__'

class ItemPhotoSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer()

    class Meta:
        model = Item_Photos
        fields = '__all__'
