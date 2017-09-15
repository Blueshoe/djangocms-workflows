from django.contrib import admin
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from .models import SimpleModel


class SimpleModelAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(SimpleModel, SimpleModelAdmin)
