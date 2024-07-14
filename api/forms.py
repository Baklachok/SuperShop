from django import forms
from api.models import Item, Item_Photos, Photo, ItemStock, Color, Size


class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = '__all__'
        widgets = {
            'categories': forms.CheckboxSelectMultiple,
        }

    def save(self, commit=True):
        item = super().save(commit=False)
        if commit:
            item.save()
            self.save_m2m()
            if self.cleaned_data['new_photos']:
                for photo in self.cleaned_data['new_photos']:
                    photo_instance = Photo.objects.create(photo=photo, name=photo.name)
                    Item_Photos.objects.create(item=item, photo=photo_instance)
        return item

class ItemStockInlineForm(forms.ModelForm):
    class Meta:
        model = ItemStock
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        item_id = None
        if 'instance' in kwargs and kwargs['instance']:
            item_id = kwargs['instance'].item.id
        elif 'initial' in kwargs and 'item' in kwargs['initial']:
            item_id = kwargs['initial']['item'].id

        if item_id:
            self.fields['color'].queryset = Color.objects.filter(item_id=item_id)
            self.fields['size'].queryset = Size.objects.filter(item_id=item_id)

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        color = cleaned_data.get('color')
        size = cleaned_data.get('size')

        if color and color.item != item:
            self.add_error('color', 'This color does not belong to the selected item.')

        if size and size.item != item:
            self.add_error('size', 'This size does not belong to the selected item.')

        return cleaned_data
