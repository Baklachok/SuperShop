from django.contrib import admin
from .models import Basket, BasketItem

class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 1


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    inlines = [BasketItemInline]


admin.site.register(BasketItem)

