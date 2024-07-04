from rest_framework import viewsets, generics, status
from rest_framework.response import Response
import logging
from .serializers import UserRegistrationSerializer
from api.models import Item
from api.serializers import ItemSerializer

logger = logging.getLogger(__name__)
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

# передавать месседж ерор
    def create(self, request, *args, **kwargs):
        logger.debug(f"Received data: {request.data}")
        print("Received data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'user': UserRegistrationSerializer(user).data,
            'message': 'Registration successful',
            'success': True,
        }, status=status.HTTP_201_CREATED)