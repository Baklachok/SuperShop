from django.db import models

from authentication.models import FrontendUser


class Address(models.Model):
    user = models.ForeignKey(FrontendUser, on_delete=models.CASCADE, related_name='addresses')
    address = models.TextField()
    lat = models.FloatField()
    lon = models.FloatField()
    default_state = models.BooleanField(default=False)

    def __str__(self):
        return self.address

