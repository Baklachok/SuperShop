from django import forms
from django.contrib import admin

from api.forms import ItemForm, ItemStockInlineForm
from api.models import Item, Category, Item_Photos, Photo, Color, Size, ItemStock
from api.widjets import ColorPickerWidget

admin.site.register(Photo)
admin.site.register(Size)

class ItemColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = '__all__'
        widgets = {
            'hex': ColorPickerWidget,
        }

class Item_PhotosInlineForm(forms.ModelForm):
    class Meta:
        model = Item_Photos
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['photo'].disabled = True


class Item_PhotosInline(admin.TabularInline):
    model = Item_Photos
    form = Item_PhotosInlineForm
    extra = 1
    readonly_fields = ('is_general_one', 'is_general_two')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "photo":
            # Получаем форму для текущего инлайна
            form = self.form(request.POST, request.FILES, instance=kwargs.get('obj', None))
            if form.fields['photo'].disabled:
                kwargs["queryset"] = Photo.objects.filter(pk=form.instance.photo.pk)
            else:
                item_id = request.resolver_match.kwargs.get('object_id')
                if item_id:
                    kwargs["queryset"] = Photo.objects.filter(item_photo__item__id=item_id) | Photo.objects.filter(item_photo__isnull=True)
                else:
                    kwargs["queryset"] = Photo.objects.filter(item_photo__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ItemStockInline(admin.TabularInline):
    model = ItemStock
    form = ItemStockInlineForm
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['color', 'size']:
            item_id = request.resolver_match.kwargs.get('object_id')
            if item_id:
                if db_field.name == 'color':
                    kwargs["queryset"] = Color.objects.filter(item_id=item_id)
                elif db_field.name == 'size':
                    kwargs["queryset"] = Size.objects.filter(item_id=item_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = ItemForm
    list_display = ('name', 'description', 'price',  'rating','order_count',
                    'discount', 'price_with_discount', 'general_photo_one', 'general_photo_two',)
    readonly_fields = ('price_with_discount', )
    list_filter = ('categories',)
    inlines = [Item_PhotosInline, ItemStockInline]

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

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    form = ItemColorForm
    list_display = ('item', 'name', 'hex')

