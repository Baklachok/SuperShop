from rest_framework import serializers

from user_profile.models import Address, ReviewPhoto, Review


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user', 'address', 'lat', 'lon', 'default_state']


class ReviewPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewPhoto
        fields = ['id', 'photo']

class ReviewSerializer(serializers.ModelSerializer):
    photos = ReviewPhotoSerializer(many=True, read_only=True)
    uploaded_photos = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True, max_length=5
    )

    class Meta:
        model = Review
        fields = ['id', 'user', 'item', 'grade', 'text', 'photos', 'uploaded_photos']

    def create(self, validated_data):
        uploaded_photos = validated_data.pop('uploaded_photos')
        review = Review.objects.create(**validated_data)
        for photo in uploaded_photos:
            ReviewPhoto.objects.create(review=review, photo=photo)
        return review

    def update(self, instance, validated_data):
        uploaded_photos = validated_data.pop('uploaded_photos', None)
        instance.grade = validated_data.get('grade', instance.grade)
        instance.text = validated_data.get('text', instance.text)
        instance.save()

        if uploaded_photos:
            instance.photos.all().delete()
            for photo in uploaded_photos:
                ReviewPhoto.objects.create(review=instance, photo=photo)

        return instance

