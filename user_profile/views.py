import logging
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from authentication.backends import CookieJWTAuthentication
from user_profile.models import Address, Review, ReviewPhoto
from user_profile.serializers import AddressSerializer, ReviewSerializer, ReviewPhotoSerializer

# Настройка логирования
logger = logging.getLogger(__name__)


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        logger.info(f"Создание нового адреса пользователем {self.request.user.id}")
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            logger.info(f"Адрес успешно создан для пользователя {request.user.id}")
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        logger.error(f"Ошибка создания адреса: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        item_id = self.request.query_params.get('item')
        if item_id:
            return self.queryset.filter(item_id=item_id)
        return self.queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                review = serializer.save(user=request.user)
                logger.info(f"Отзыв {review.id} создан пользователем {request.user.id} для товара {review.item.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Ошибка при создании отзыва: {str(e)}")
                return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(f"Ошибка валидации при создании отзыва: {serializer.errors}")
        return Response({"error": True, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                review = serializer.save()
                logger.info(f"Отзыв {review.id} обновлён пользователем {request.user.id}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Ошибка при обновлении отзыва {instance.id}: {str(e)}")
                return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(f"Ошибка валидации при обновлении отзыва {instance.id}: {serializer.errors}")
        return Response({"error": True, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            logger.info(f"Отзыв {instance.id} удалён пользователем {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Ошибка при удалении отзыва {instance.id}: {str(e)}")
            return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        try:
            review = serializer.save(user=self.request.user)
            logger.info(f"Отзыв {review.id} создан пользователем {self.request.user.id}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении отзыва: {str(e)}")
            raise ValidationError({"error": True, "message": str(e)})

    def perform_destroy(self, instance):
        instance.delete()
        logger.info(f"Отзыв {instance.id} был удалён")


class ReviewPhotoViewSet(viewsets.ModelViewSet):
    queryset = ReviewPhoto.objects.all()
    serializer_class = ReviewPhotoSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                review_photo = serializer.save()
                logger.info(f"Фото {review_photo.id} для отзыва {review_photo.review.id} добавлено пользователем {request.user.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Ошибка при загрузке фото к отзыву: {str(e)}")
                return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(f"Ошибка валидации при загрузке фото: {serializer.errors}")
        return Response({"error": True, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                review_photo = serializer.save()
                logger.info(f"Фото {review_photo.id} обновлено пользователем {request.user.id}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Ошибка при обновлении фото {instance.id}: {str(e)}")
                return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(f"Ошибка валидации при обновлении фото {instance.id}: {serializer.errors}")
        return Response({"error": True, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            logger.info(f"Фото {instance.id} удалено пользователем {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Ошибка при удалении фото {instance.id}: {str(e)}")
            return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        instance.delete()
        logger.info(f"Фото {instance.id} было удалено")
