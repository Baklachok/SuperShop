from django.contrib import admin
from rest_framework.exceptions import ValidationError

from .models import Basket, BasketItem, FavouritesItem, Favourites


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 1

@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    inlines = [BasketItemInline]

class BasketItemAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except ValidationError as e:
            self.message_user(request, str(e), level='warning')

admin.site.register(BasketItem, BasketItemAdmin)

