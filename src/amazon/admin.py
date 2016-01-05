from django.contrib import admin

from .models import Search, Item


@admin.register(Search)
class SearchAdmin(admin.ModelAdmin):

    pass


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):

    pass
