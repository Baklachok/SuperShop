from django import forms
from api.models import Item, Item_Photos, Photo


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

