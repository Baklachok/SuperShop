
from rest_framework import viewsets, generics
import logging

from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.models import Item, Category, Photo, ItemStock
from api.pagination import CustomPagination
from api.serializers import ItemSerializer, CategorySerializer, PhotoSerializer, StockItemSerializer

logger = logging.getLogger(__name__)

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    pagination_class = CustomPagination
    permission_classes = (AllowAny,)
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            return self.queryset.filter(categories__slug=category_slug)
        return self.queryset

    def list(self, request, *args, **kwargs):
        populate = request.query_params.get('populate', '').split(',')
        queryset = self.get_queryset()

        if populate:
            if 'all_photo' in populate:
                queryset = queryset.prefetch_related('item_photos__photo')
            if 'general_photos' in populate:
                queryset = queryset.prefetch_related('general_photo_one__photo', 'general_photo_two__photo')
            if 'categories' in populate:
                queryset = queryset.prefetch_related('categories')
            if 'colors_sizes' in populate:
                queryset = queryset.prefetch_related('colors', 'sizes')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # serializer = self.get_serializer(queryset, many=True)
        return Response([])

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

class ItemDetail(generics.RetrieveAPIView):
    serializer_class = ItemSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'item_id'

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        return Item.objects.filter(categories__slug=category_slug)


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class StockItemView(generics.ListAPIView):
    serializer_class = StockItemSerializer

    def get_queryset(self):
        item_id = self.kwargs['item_id']
        return ItemStock.objects.filter(item_id=item_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'stock_items': serializer.data})
