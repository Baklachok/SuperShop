from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from autoslug import AutoSlugField
from django.db.models.signals import post_delete, post_save, pre_save
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
    _updating = False

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
        if not self._updating:
            self._updating = True

            if self.is_general_one:
                Item_Photos.objects.filter(item=self.item).exclude(pk=self.pk).update(is_general_one=False)
            if self.is_general_two:
                Item_Photos.objects.filter(item=self.item).exclude(pk=self.pk).update(is_general_two=False)

            super().save(*args, **kwargs)

            if self.is_general_one:
                self.item.general_photo_one = self
            if self.is_general_two:
                self.item.general_photo_two = self

            else:
                if not self.is_general_one and self.item.general_photo_one == self:
                    self.item.general_photo_one = None
                if not self.is_general_two and self.item.general_photo_two == self:
                    self.item.general_photo_two = None

            if not self.item._updating:
                self.item._updating = True
                self.item.save(update_fields=['general_photo_one', 'general_photo_two'])
                self.item._updating = False

            self._updating = False
    def __str__(self):
        return f'{self.item.name} - {self.photo.name}'

@receiver(post_delete, sender=Item_Photos)
def delete_orphaned_photos(sender, instance, **kwargs):
    # Delete the photo if it's not referenced by any other Item_Photos
    if not Item_Photos.objects.filter(photo=instance.photo).exists():
        instance.photo.delete()

@receiver(post_save, sender=Item_Photos)
def update_item_general_photos(sender, instance, created, **kwargs):
    if not instance.item:
        return

    if instance.is_general_one:
        instance.item.general_photo_one = instance
    else:
        if instance.item.general_photo_one == instance:
            instance.item.general_photo_one = None

    if instance.is_general_two:
        instance.item.general_photo_two = instance
    else:
        if instance.item.general_photo_two == instance:
            instance.item.general_photo_two = None

    instance.item.save(update_fields=['general_photo_one', 'general_photo_two'])

@receiver(post_delete, sender=Item_Photos)
def clear_item_general_photos(sender, instance, **kwargs):
    if not instance.item:
        return

    if instance.item.general_photo_one == instance:
        instance.item.general_photo_one = None
        instance.item.save(update_fields=['general_photo_one'])

    if instance.item.general_photo_two == instance:
        instance.item.general_photo_two = None
        instance.item.save(update_fields=['general_photo_two'])

@receiver(post_delete, sender=Photo)
def delete_photo_file(sender, instance, **kwargs):
    instance.photo.delete(save=False)

@receiver(post_delete, sender=Category)
def delete_category_photo_file(sender, instance, **kwargs):
    instance.photo.delete(save=False)

@receiver(pre_save, sender=Photo)
def delete_old_photo_file(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_instance = Photo.objects.get(pk=instance.pk)
    except Photo.DoesNotExist:
        return False

    if old_instance.photo and old_instance.photo != instance.photo:
        old_instance.photo.delete(save=False)

@receiver(pre_save, sender=Category)
def delete_old_category_photo_file(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_instance = Category.objects.get(pk=instance.pk)
    except Photo.DoesNotExist:
        return False

    if old_instance.photo and old_instance.photo != instance.photo:
        old_instance.photo.delete(save=False)
