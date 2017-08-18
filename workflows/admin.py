# -*- coding: utf-8 -*-

from adminsortable2.admin import SortableInlineAdminMixin
from cms.admin.pageadmin import PageAdmin
from cms.extensions.admin import TitleExtensionAdmin
from cms.models import Page, Title
from cms.utils.urlutils import admin_reverse
from django.conf.urls import url
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from workflows.models import WorkflowExtension, Action
from workflows.views import WORKFLOW_VIEWS
from .models import WorkflowStage, Workflow


# Register your models here.


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


admin.site.register(Workflow, WorkflowAdmin)


class WorkflowExtensionAdmin(TitleExtensionAdmin):
    pass


admin.site.register(WorkflowExtension, WorkflowExtensionAdmin)


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

try:
    admin.site.unregister(Page)
finally:
    admin.site.register(Page, WorkflowPageAdmin)


class ActionAdmin(admin.ModelAdmin):
    change_form_template = 'admin/action_change_form.html'
    list_display = ['__str__', 'title', 'status_display', 'created', 'requires_action', 'page_link']
    readonly_fields = ['title', 'workflow', 'user', 'message', 'created', 'status_display', 'page_link']
    fields = [('title', 'workflow', 'user', 'created'), 'message', 'status_display', 'page_link']

    class Media:
        js = ['js/close_sideframe.js']

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
    requires_action.short_description = _('Requires action')

    def page_link(self, instance):
        t = instance.title
        # t = Title()
        opts = Page._meta
        return mark_safe('<a href="{link}" target="_top" class="link">{label}</a>'.format(
            link=admin_reverse(
                '{}_{}_preview_page'.format(opts.app_label, opts.model_name),
                args=(t.page_id, t.language)
            ),
            # link=t.page.get_absolute_url(language=t.language),
            label=_('View page')
        ))
    page_link.short_description = ''

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra = extra_context or {}
        extra.update(self.extra_context(request, object_id))
        return super(ActionAdmin, self).change_view(request, object_id, form_url=form_url, extra_context=extra)

    def extra_context(self, request, object_id):
        action = self.get_object(request, object_id)
        actions = action.get_descendants().order_by('depth')
        return {'actions': actions}
    #
    # def goto_page(self, request, *args, **kwargs):


admin.site.register(Action, ActionAdmin)
