from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from autoslug import AutoSlugField
from django.db.models.signals import pre_delete, post_delete, post_save, pre_save
from django.dispatch import receiver
from unidecode import unidecode

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from='get_slug', unique=True, always_update=True, default='temp-slug')
    photo = models.ImageField(upload_to='categories/', blank=True)

    def get_slug(self):
        return unidecode(self.name)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    categories = models.ManyToManyField(Category, related_name='items')
    rating = models.DecimalField(max_digits=2, decimal_places=1,
                                 validators=[MinValueValidator(0), MaxValueValidator(5)], default=0)
    order_count = models.PositiveIntegerField(default=0)
    discount = models.DecimalField(max_digits=3, decimal_places=2,
                                   validators=[MinValueValidator(0), MaxValueValidator(1)], default=0)
    price_with_discount = models.DecimalField(max_digits=10, decimal_places=2,
                                              validators=[MinValueValidator(0)], default=0,
                                              editable=False)
    general_photo_one = models.OneToOneField('Item_Photos', on_delete=models.SET_NULL,
                                             related_name='item_general_photo_one',
                                             limit_choices_to={'is_general_one': True}, blank=True,
                                             null=True)
    general_photo_two = models.OneToOneField('Item_Photos', on_delete=models.SET_NULL,
                                             related_name='item_general_photo_two',
                                             limit_choices_to={'is_general_two': True}, blank=True,
                                             null=True)

    def save(self, *args, **kwargs):
        self.price_with_discount = self.price * (1 - self.discount)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Photo(models.Model):
    name = models.CharField(max_length=100, unique=True)
    photo = models.ImageField(upload_to='item/', blank=True)

    def __str__(self):
        return self.name

class Item_Photos(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='item_photos')
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE,  related_name='item_photo')
    is_general_one = models.BooleanField(default=False)
    is_general_two = models.BooleanField(default=False)
    _updating = False

    def save(self, *args, **kwargs):
        if not self._updating:  # Check if this instance is already being updated
            self._updating = True  # Set the flag to indicate update in progress

            if self.is_general_one or self.is_general_two:
                # Reset other general flags for the same item if setting a new general photo
                Item_Photos.objects.filter(item=self.item).exclude(pk=self.pk).update(is_general_one=False,
                                                                                      is_general_two=False)

            super().save(*args, **kwargs)

            if self.is_general_one:
                self.item.general_photo_one = self
            elif self.is_general_two:
                self.item.general_photo_two = self
            self.item.save(update_fields=['general_photo_one', 'general_photo_two'])

            self._updating = False  # Reset the flag after update

    def __str__(self):
        return f'{self.item.name} - {self.photo.name}'

@receiver(post_delete, sender=Item_Photos)
def delete_orphaned_photos(sender, instance, **kwargs):
    # Delete the photo if it's not referenced by any other Item_Photos
    if not Item_Photos.objects.filter(photo=instance.photo).exists():
        instance.photo.delete()

@receiver(post_save, sender=Item)
def update_general_photo_flags(sender, instance, **kwargs):
    if not instance.general_photo_one and instance.item_photos.filter(is_general_one=True).exists():
        instance.item_photos.filter(is_general_one=True).update(is_general_one=False)
    if not instance.general_photo_two and instance.item_photos.filter(is_general_two=True).exists():
        instance.item_photos.filter(is_general_two=True).update(is_general_two=False)

@receiver(pre_save, sender=Item)
def update_general_photo_flags_before_save(sender, instance, **kwargs):
    # Проверка и обновление флагов перед сохранением
    if instance.pk:
        old_instance = Item.objects.get(pk=instance.pk)
        if old_instance.general_photo_one and not instance.general_photo_one:
            old_instance.general_photo_one.is_general_one = False
            old_instance.general_photo_one.save(update_fields=['is_general_one'])
        if old_instance.general_photo_two and not instance.general_photo_two:
            old_instance.general_photo_two.is_general_two = False
            old_instance.general_photo_two.save(update_fields=['is_general_two'])
