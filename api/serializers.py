from rest_framework import serializers

from .models import Item, Category, Photo, Item_Photos, Color, Size, ItemStock


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='category-detail', lookup_field='slug')
    items_url = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'


    def get_items_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/api/categories/{obj.slug}/items/')

    def get_item_count(self, obj):
        return obj.items.count()

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = '__all__'

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['name', 'hex']


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['name']

class ItemPhotoSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer()

    class Meta:
        model = Item_Photos
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    colors = ColorSerializer(many=True, read_only=True)
    sizes = SizeSerializer(many=True, read_only=True)
    class Meta:
        model = Item
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        if request and request.query_params.get('populate') == 'all_photo':
            representation['all_photo'] = ItemPhotoSerializer(instance.item_photos.all(), many=True).data
        else:
            representation['all_photos'] = list(instance.item_photos.values_list('id', flat=True))

        if request and request.query_params.get('populate') == 'general_photos':
            representation['general_photo_one'] = ItemPhotoSerializer(
                instance.general_photo_one).data if instance.general_photo_one else None
            representation['general_photo_two'] = ItemPhotoSerializer(
                instance.general_photo_two).data if instance.general_photo_two else None

        if request and request.query_params.get('populate') == 'categories':
            representation['categories'] = CategorySerializer(instance.categories.all(), many=True, context={'request': request}).data

        if request and request.query_params.get('populate') == 'colors_sizes':
            representation['colors'] = ColorSerializer(instance.colors.all(), many=True).data
            representation['sizes'] = SizeSerializer(instance.sizes.all(), many=True).data
        else:
            representation['colors'] = []
            representation['sizes'] = []

        return representation


class StockItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(source='item.id')
    color = serializers.CharField(source='color.name')
    hex = serializers.CharField(source='color.hex')
    size = serializers.CharField(source='size.name')

    class Meta:
        model = ItemStock
        fields = ['item_id', 'color', 'hex', 'size', 'quantity']
