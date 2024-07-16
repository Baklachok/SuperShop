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

class StockItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(source='item.id')
    color = serializers.CharField(source='color.name')
    hex = serializers.CharField(source='color.hex')
    size = serializers.CharField(source='size.name')

    class Meta:
        model = ItemStock
        fields = ['item_id', 'color', 'hex', 'size', 'quantity']

class ItemSerializer(serializers.ModelSerializer):
    colors = ColorSerializer(many=True, read_only=True)
    sizes = SizeSerializer(many=True, read_only=True)
    class Meta:
        model = Item
        fields = '__all__'

    def get_colors(self, instance):
        colors = instance.stocks.values('color__name', 'color__hex').distinct()
        return [{'name': color['color__name'], 'hex': color['color__hex']} for color in colors]

    def get_sizes(self, instance):
        sizes = instance.stocks.values('size__name').distinct()
        return [{'name': size['size__name']} for size in sizes]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        populate = request.query_params.get('populate', '').split(',') if request else []

        if 'all_photo' in populate:
            representation['all_photo'] = ItemPhotoSerializer(instance.item_photos.all(), many=True).data
        else:
            representation['all_photos'] = list(instance.item_photos.values_list('id', flat=True))

        if 'general_photos' in populate:
            representation['general_photo_one'] = ItemPhotoSerializer(
                instance.general_photo_one).data if instance.general_photo_one else None
            representation['general_photo_two'] = ItemPhotoSerializer(
                instance.general_photo_two).data if instance.general_photo_two else None

        if 'categories' in populate:
            representation['categories'] = CategorySerializer(instance.categories.all(), many=True,
                                                              context={'request': request}).data

        if 'colors_sizes' in populate:
            representation['colors'] = self.get_colors(instance)
            representation['sizes'] = self.get_sizes(instance)
        else:
            representation['colors'] = []
            representation['sizes'] = []

        return representation
