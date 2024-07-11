from django import forms
from django.contrib import admin

from api.models import Item, Category, Item_Photos, Photo

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
    list_display = ('name', 'description', 'price',  'rating','order_count',
                    'discount', 'price_with_discount', 'general_photo_one', 'general_photo_two',)
    readonly_fields = ('price_with_discount',  'all_photos')
    list_filter = ('categories',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['general_photo_one', 'general_photo_two']:
            item_id = request.resolver_match.kwargs.get('object_id')
            if item_id:
                kwargs["queryset"] = Item_Photos.objects.filter(item_id=item_id)
            else:
                kwargs["queryset"] = Item_Photos.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update_general_photos()

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Item_Photos)
class ItemPhotosAdmin(admin.ModelAdmin):
    list_display = ('item', 'photo', 'is_general_one', 'is_general_two' )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['item', 'photo', 'is_general_one', 'is_general_two']
        else:
            return ['is_general_one', 'is_general_two']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "photo":
            if not request.resolver_match.kwargs.get('object_id'):
                kwargs["queryset"] = Photo.objects.filter(item_photo__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
