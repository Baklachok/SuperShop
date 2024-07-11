from rest_framework import viewsets, generics, status
from rest_framework.response import Response
import logging


from api.models import Item, Category
from api.serializers import ItemSerializer, CategorySerializer


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



# class UserRegistrationView(generics.CreateAPIView):
#     serializer_class = UserRegistrationSerializer
#
# # передавать месседж ерор
#     def create(self, request, *args, **kwargs):
#         logger.debug(f"Received data: {request.data}")
#         print("Received data: {request.data}")
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()
#         return Response({
#             'user': UserRegistrationSerializer(user).data,
#             'message': 'Registration successful',
#             'success': True,
#         }, status=status.HTTP_201_CREATED)