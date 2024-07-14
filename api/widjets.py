from django import forms


class ColorPickerWidget(forms.TextInput):
    input_type = 'color'

    def __init__(self, attrs=None):
        default_attrs = {'style': 'width: 70px; height: 30px; padding: 0;'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)