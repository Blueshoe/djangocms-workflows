# -*- coding: utf-8 -*-

from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin

from .models import PipelineStage

# Register your models here.


class PipelineStageInline(SortableInlineAdminMixin, admin.TabularInline):
    # TODO
    # formset = WorkflowStepInlineFormSet
    model = PipelineStage

    def get_extra(self, request, obj=None, **kwargs):
        if obj and obj.pk:
            return 0
        return 1


class PipelineAdmin(admin.ModelAdmin):
    # TODO
    inlines = [PipelineStageInline]
    list_display = ['name', 'default']
    fields = ['name', 'is_default']


# TODO more required admins: TitleExtensionAdmin, PageAdmin
