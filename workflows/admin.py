# -*- coding: utf-8 -*-

from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin

from .models import WorkflowStage

# Register your models here.


class WorkflowStageInline(SortableInlineAdminMixin, admin.TabularInline):
    # TODO
    # formset = WorkflowStepInlineFormSet
    model = WorkflowStage

    def get_extra(self, request, obj=None, **kwargs):
        if obj and obj.pk:
            return 0
        return 1


class WorkflowAdmin(admin.ModelAdmin):
    # TODO
    inlines = [WorkflowStageInline]
    list_display = ['name', 'default']
    fields = ['name', 'is_default']


# TODO more required admins: TitleExtensionAdmin, PageAdmin
