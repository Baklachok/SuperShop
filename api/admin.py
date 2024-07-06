from django import forms
from django.contrib import admin

from api.models import Item, Category

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
    readonly_fields = ('price_with_discount',)
    list_filter = ('categories',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)