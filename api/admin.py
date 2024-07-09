from django import forms
from django.contrib import admin

from api.models import Item, Category, Item_Photos, Photo

admin.site.register(Item_Photos)
admin.site.register(Photo)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'
        widgets = {
            'categories': forms.CheckboxSelectMultiple,
        }

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):

    form = ItemForm
    list_display = ('name', 'description', 'price',  'rating', 'order_count', 'discount', 'price_with_discount')
    readonly_fields = ('price_with_discount', 'general_photo_one', 'general_photo_two',)
    list_filter = ('categories',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

