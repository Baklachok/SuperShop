from rest_framework import viewsets
import logging


from api.models import Item, Category, Photo
from api.serializers import ItemSerializer, CategorySerializer, PhotoSerializer

logger = logging.getLogger(__name__)
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            return self.queryset.filter(categories__slug=category_slug)
        return self.queryset

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
