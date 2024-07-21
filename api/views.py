
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
        queryset = self.queryset
        category_slug = self.kwargs.get('category_slug')

        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        with_discount = self.request.query_params.get('with_discount')
        in_stock = self.request.query_params.get('in_stock')
        sort = self.request.query_params.get('sort')

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if with_discount:
            queryset = queryset.filter(discount__gt=0)

        if in_stock:
            queryset = queryset.filter(stocks__quantity__gt=0).distinct()

        if sort:
            if sort == 'discount':
                queryset = queryset.order_by('-discount')
            elif sort == 'price_asc':
                queryset = queryset.order_by('price')
            elif sort == 'price_desc':
                queryset = queryset.order_by('-price')
        else:
            queryset = queryset.order_by('-order_count')

        return queryset

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
                queryset = queryset.prefetch_related('stocks__color', 'stocks__size')

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
        queryset = ItemStock.objects.filter(item_id=item_id)

        colors = self.request.query_params.get('color')
        sizes = self.request.query_params.get('size')

        if colors:
            colors = colors.split(',')
            queryset = queryset.filter(color__name__in=colors)

        if sizes:
            sizes = sizes.split(',')
            queryset = queryset.filter(size__name__in=sizes)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'stock_items': serializer.data})
