# -*- coding: utf-8 -*-

from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import WorkflowStage, Workflow


# Register your models here.


class WorkflowStageInline(SortableInlineAdminMixin, admin.TabularInline):
    # formset = WorkflowStepInlineFormSet
    model = WorkflowStage

    def get_extra(self, request, obj=None, **kwargs):

        if obj and obj.pk:
            return 0
        return 1


class WorkflowAdmin(admin.ModelAdmin):
    inlines = [WorkflowStageInline]
    fields = ['name', 'default']
    list_display = ['name', 'default', 'list_stages']

    class Media:
        # fixes display bug in sortable admin tabular inline
        css = {
            'all': ('sortable_inline/sortable_inline.css',)
        }

    def list_stages(self, obj):
        return mark_safe(' '.join(self._stage_display(stage) for stage in obj.stages.all()))
    list_stages.short_description = _('Stages')

    def _stage_display(self, stage):
        s = stage.group.name
        if stage.order > 1:
            s = '&rarr; {}'.format(s)
        if stage.optional:
            s = '[{}]'.format(s)
        return s

    def get_queryset(self, request):
        qs = super(WorkflowAdmin, self).get_queryset(request)
        qs = qs.prefetch_related('stages')
        return qs


# TODO more required admins: TitleExtensionAdmin, PageAdmin

admin.site.register(Workflow, WorkflowAdmin)
