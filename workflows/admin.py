# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from adminsortable2.admin import SortableInlineAdminMixin
from cms.admin.pageadmin import PageAdmin
from cms.extensions.admin import TitleExtensionAdmin
from cms.models import Page, Title
from django.conf.urls import url
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import WorkflowExtension, Action,WorkflowStage, Workflow
from .views import WORKFLOW_VIEWS


# Register your models here.
# def get_page_admin():
#     pa = admin.site._registry.pop(Page, PageAdmin)
#     print(pa)
#     return pa.__class__


class WorkflowStageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = WorkflowStage

    def get_extra(self, request, obj=None, **kwargs):
        return not (obj and obj.pk)


class WorkflowAdmin(admin.ModelAdmin):
    inlines = [WorkflowStageInline]
    fields = ['name', 'default']
    list_display = ['name', 'default', 'list_stages']

    class Media:
        # fixes display bug in sortable admin tabular inline
        css = {
            'all': ('workflows/css/sortable_inline.css',)
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


class WorkflowExtensionAdmin(TitleExtensionAdmin):
    pass


class WorkflowPageAdmin(PageAdmin):
    WORKFLOW_URL_PATTERN = r'^([0-9]+)/([a-z\-]+)/wf/{}/$'
    WORKFLOW_URL_NAME = 'workflow_{}'

    OPEN_REQUEST_MESSAGE = _('Current changes have not yet been approved.')
    NOT_REQUESTED_MESSAGE = _('Current changes must be submitted for approval.')

    def get_urls(self):
        urls = []
        # add workflow action views
        for action_type, view in WORKFLOW_VIEWS.items():
            pattern = self.WORKFLOW_URL_PATTERN.format(action_type)
            name = self.WORKFLOW_URL_NAME.format(action_type)
            urls.append(url(pattern, self.admin_site.admin_view(view.as_view()), name=name))
        return urls + super(WorkflowPageAdmin, self).get_urls()

    def publish_page(self, request, page_id, language):
        title = get_object_or_404(Title, page_id=page_id, language=language, publisher_is_draft=True)
        workflow = Workflow.get_workflow(title)
        current_request = Action.get_current_request(title)

        # legal publishing scenarios: no workflow defined for title OR current request is open and approved
        if not workflow or (current_request and current_request.is_publishable()):
            return super(WorkflowPageAdmin, self).publish_page(request, page_id, language)

        # illegal publishing scenarios: current request not approved or no request at all
        if current_request:
            messages.warning(request, self.OPEN_REQUEST_MESSAGE)
        else:
            messages.warning(request, self.NOT_REQUESTED_MESSAGE)

        return redirect(title.page.get_absolute_url(language, fallback=True))


class ActionAdmin(admin.ModelAdmin):
    # custom templates
    change_form_template = 'workflows/admin/action_change_form.html'
    change_list_template = 'workflows/admin/action_change_list.html'

    readonly_fields = ['title', 'workflow', 'status_display', 'page_link', 'requires_action']
    list_display = ['__str__', 'title', 'status_display', 'created', 'requires_action', 'page_link']
    fieldsets = (
        (None, {
            'fields': (('title', 'workflow', 'status_display', 'requires_action'),),
            'classes': ('wide',)
        }),
        (_('Actions'), {
            'fields': ('page_link',)
        })
    )

    # newest requests first
    ordering = ['-created']

    class Media:
        css = {
            'all': ('workflows/css/action_admin.css',)
        }

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        self.request = request
        qs = super(ActionAdmin, self).get_queryset(request)
        qs = qs.filter(depth=1)
        return qs

    def requires_action(self, instance):
        return self.request.user in instance.last_action().next_mandatory_stage_editors()
    requires_action.short_description = _('Requires your action')
    requires_action.boolean = True

    def page_link(self, instance):
        t = instance.title
        return mark_safe('<a href="{link}" target="_top" class="close-sideframe-link">{label}</a>'.format(
            link=t.page.get_draft_url(language=t.language, fallback=False),
            label=_('View page')
        ))
    page_link.short_description = _('View page in browser')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra = extra_context or {}
        extra.update(self.extra_context(request, object_id))
        return super(ActionAdmin, self).change_view(request, object_id, form_url=form_url, extra_context=extra)

    def extra_context(self, request, object_id):
        action = self.get_object(request, object_id)
        actions = Action.get_tree(parent=action).order_by('depth')
        return {'actions': actions}


if admin.site.is_registered(Page):
    admin.site.unregister(Page)

admin.site.register(Page, WorkflowPageAdmin)
admin.site.register(Workflow, WorkflowAdmin)
admin.site.register(WorkflowExtension, WorkflowExtensionAdmin)
admin.site.register(Action, ActionAdmin)
