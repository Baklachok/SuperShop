from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from authentication.backends import CookieJWTAuthentication
from user_profile.models import Address, Review, ReviewPhoto
from user_profile.serializers import AddressSerializer, ReviewSerializer, ReviewPhotoSerializer


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [CookieJWTAuthentication, ]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReviewPhotoViewSet(viewsets.ModelViewSet):
    queryset = ReviewPhoto.objects.all()
    serializer_class = ReviewPhotoSerializer

