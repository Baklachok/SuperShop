from django.contrib import admin

from api.models import Item, MyUser


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price')


# @admin.register(MyUser)
# class MyUserAdmin(admin.ModelAdmin):
#     list_display = ('name', 'telNo')
#     search_fields = ('name', 'telNo')