from django.http import JsonResponse
from rest_framework import viewsets, generics
import logging

from rest_framework.response import Response

from api.models import Item, Category, Photo
from api.pagination import CustomPagination
from api.serializers import ItemSerializer, CategorySerializer, PhotoSerializer

logger = logging.getLogger(__name__)

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    pagination_class = CustomPagination
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            return self.queryset.filter(categories__slug=category_slug)
        return self.queryset

    def list(self, request, *args, **kwargs):
        populate = request.query_params.get('populate')
        queryset = self.get_queryset()

        if populate:
            for field in populate.split(','):
                queryset = queryset.select_related(field)

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
