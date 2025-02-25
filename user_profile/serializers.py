import logging
import traceback

from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from user_profile.models import Address, ReviewPhoto, Review

logger = logging.getLogger(__name__)

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user', 'address', 'lat', 'lon', 'default_state']


class ReviewPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewPhoto
        fields = '__all__'



class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_photo = serializers.ImageField(source='user.profile_picture', read_only=True)
    photos = ReviewPhotoSerializer(many=True, read_only=True)
    uploaded_photos = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True, max_length=5, required=False
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Review
        fields = ['item', 'grade', 'comments', 'photos', 'uploaded_photos', 'advantages', 'disadvantages', 'user_name',
                  'user_photo', 'created_at']

    def create(self, validated_data):
        uploaded_photos = validated_data.pop('uploaded_photos', [])
        review = Review.objects.create(**validated_data)
        for photo in uploaded_photos:
            ReviewPhoto.objects.create(review=review, photo=photo)
        return review

    def update(self, instance, validated_data):
        uploaded_photos = validated_data.pop('uploaded_photos', None)
        instance.grade = validated_data.get('grade', instance.grade)
        instance.comments = validated_data.get('comments', instance.comments)
        instance.save()

        if uploaded_photos:
            instance.photos.all().delete()
            for photo in uploaded_photos:
                ReviewPhoto.objects.create(review=instance, photo=photo)

        return instance

