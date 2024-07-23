from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from api.models import Item
from authentication.models import FrontendUser


class Address(models.Model):
    user = models.ForeignKey(FrontendUser, on_delete=models.CASCADE, related_name='addresses')
    address = models.TextField()
    lat = models.FloatField()
    lon = models.FloatField()
    default_state = models.BooleanField(default=False)

    def __str__(self):
        return self.address

class Review(models.Model):
    user = models.ForeignKey(FrontendUser, on_delete=models.CASCADE, related_name='review')
    item = models.ForeignKey(Item, related_name='review', on_delete=models.CASCADE)
    grade = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    text = models.TextField()

    def __str__(self):
        return f'Review by {self.user} for {self.item}'


class ReviewPhoto(models.Model):
    review = models.ForeignKey(Review, related_name='photos', on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='review_photos/')

    def __str__(self):
        return f'Photo for review {self.review.id}'