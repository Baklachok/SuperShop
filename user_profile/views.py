from django.shortcuts import render
from rest_framework import viewsets, permissions

from authentication.backends import CookieJWTAuthentication
from user_profile.models import Address
from user_profile.serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
