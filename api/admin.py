from django.contrib import admin

from api.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'category', 'rating', 'order_count', 'discount', 'price_with_discount')
    readonly_fields = ('price_with_discount',)
