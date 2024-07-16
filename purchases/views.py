from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated

from authentication.backends import CookieJWTAuthentication
from .models import Basket, BasketItem
from .serializers import BasketSerializer, BasketItemSerializer


class BasketViewSet(viewsets.ModelViewSet):
    authentication_classes = [CookieJWTAuthentication, ]
    serializer_class = BasketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Basket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
