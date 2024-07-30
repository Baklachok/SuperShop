from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from autoslug import AutoSlugField
from django.db.models import Sum, Avg
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from django import forms
from django.urls import reverse
from django.utils.html import format_html
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
                                             related_name='item_general_photo_one', blank=True,
                                             null=True)
    general_photo_two = models.OneToOneField('Item_Photos', on_delete=models.SET_NULL,
                                             related_name='item_general_photo_two', blank=True,
                                             null=True)
    information = models.TextField(blank=True)
    brand = models.TextField(blank=True)
    feature = models.TextField(blank=True)
    size_table = models.TextField(blank=True)
    _updating = False

    def save(self, *args, **kwargs):
        self.skip_update = kwargs.pop('skip_update', False)
        self.price_with_discount = self.price * (1 - self.discount)
        super().save(*args, **kwargs)
        if not self.skip_update:
            self.update_general_photos()

    def update_general_photos(self):
        if not self._updating:
            self._updating = True

            if self.general_photo_one:
                Item_Photos.objects.filter(item=self, is_general_one=True).exclude(pk=self.general_photo_one.pk).update(is_general_one=False)
                self.general_photo_one.is_general_one = True
                self.general_photo_one.save(update_fields=['is_general_one'])
            else:
                Item_Photos.objects.filter(item=self, is_general_one=True).update(
                    is_general_one=False)

            if self.general_photo_two:
                Item_Photos.objects.filter(item=self, is_general_two=True).exclude(pk=self.general_photo_two.pk).update(is_general_two=False)
                self.general_photo_two.is_general_two = True
                self.general_photo_two.save(update_fields=['is_general_two'])
            else:
                Item_Photos.objects.filter(item=self, is_general_two=True).update(
                    is_general_two=False)

            self._updating = False

    def __str__(self):
        return self.name

    def available_colors(self):
        return Color.objects.filter(itemstock__item=self).distinct()

    def available_sizes(self):
        return Size.objects.filter(itemstock__item=self).distinct()

    def get_stock(self, color=None, size=None):
        queryset = ItemStock.objects.filter(item=self)
        if color:
            queryset = queryset.filter(color=color)
        if size:
            queryset = queryset.filter(size=size)
        return queryset.aggregate(total=Sum('quantity'))['total']

    @property
    def all_photos(self):
        return format_html(
            ", ".join([
                '<a href="{}">{}</a>'.format(
                    reverse('admin:api_item_photos_change', args=[photo.pk]),
                    photo.photo.name
                )
                for photo in self.item_photos.all()
            ])
        )

    def update_rating(self):
        avg_rating = self.review.aggregate(average=Avg('grade'))['average']
        self.rating = avg_rating if avg_rating else 0
        self.save(update_fields=['rating'])


class Photo(models.Model):
    name = models.CharField(max_length=100, unique=True)
    photo = models.ImageField(upload_to='item/', blank=True, default='default.png')

    def __str__(self):
        return self.name


class Item_Photos(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='item_photos')
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE,  related_name='item_photo')
    is_general_one = models.BooleanField(default=False)
    is_general_two = models.BooleanField(default=False)
    _updating = False

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', None)

        if not hasattr(self, '_updating'):
            self._updating = True

            if update_fields:
                if 'is_general_one' in update_fields:
                    if self.is_general_one:
                        self.item.general_photo_one = self
                    else:
                        if self.item.general_photo_one == self:
                            self.item.general_photo_one = None
                    self.item.save(update_fields=['general_photo_one'])

                if 'is_general_two' in update_fields:
                    if self.is_general_two:
                        self.item.general_photo_two = self
                    else:
                        if self.item.general_photo_two == self:
                            self.item.general_photo_two = None
                    self.item.save(update_fields=['general_photo_two'])

        super(Item_Photos, self).save(*args, **kwargs)
    def __str__(self):
        return f'{self.item.name} - {self.photo.name}'

class Color(models.Model):
    name = models.CharField(max_length=30)
    hex = models.CharField(max_length=7, default='#FF0000')

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class ItemStock(models.Model):
    item = models.ForeignKey(Item, related_name='stocks', on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    _deleting = False  # Внутренний флаг для предотвращения рекурсивного удаления

    def __str__(self):
        return f"{self.item.name} - {self.color.name} - {self.size.name}"


@receiver(post_delete, sender=Item_Photos)
def delete_orphaned_photos(sender, instance, **kwargs):
    if not Item_Photos.objects.filter(photo=instance.photo).exists():
        instance.photo.delete()

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

@receiver(post_delete, sender=ItemStock)
def delete_empty_item_stock(sender, instance, **kwargs):
    if instance.quantity == 0:
        instance.delete()

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

@receiver(pre_save, sender=Item)
def update_item_general_photos_on_save(sender, instance, **kwargs):
    with transaction.atomic():
        old_instance = sender.objects.filter(pk=instance.pk).first()

        if old_instance:
            if not hasattr(old_instance, '_updating'):
                old_instance._updating = True

                if old_instance.general_photo_one != instance.general_photo_one:
                    if old_instance.general_photo_one:
                        old_instance.general_photo_one.is_general_one = False
                        old_instance.general_photo_one.save(update_fields=['is_general_one'])
                    if instance.general_photo_one:
                        instance.general_photo_one.is_general_one = True
                        instance.general_photo_one.save(update_fields=['is_general_one'])


                if old_instance.general_photo_two != instance.general_photo_two:
                    if old_instance.general_photo_two:
                        old_instance.general_photo_two.is_general_two = False
                        old_instance.general_photo_two.save(update_fields=['is_general_two'])
                    if instance.general_photo_two:
                        instance.general_photo_two.is_general_two = True
                        instance.general_photo_two.save(update_fields=['is_general_two'])


