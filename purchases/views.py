from rest_framework import viewsets, permissions
from .models import Basket, BasketItem
from .serializers import BasketSerializer, BasketItemSerializer

class BasketViewSet(viewsets.ModelViewSet):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Basket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

