# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cms.models import Page, Title
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from .email import send_action_mails
from .forms import ActionForm
from .models import Action, Workflow


NO_WORKFLOW = _('There is no workflow for this page and language.')
ACTIVE_REQUEST = _('There already is an active request for this page and language.')
NO_ACTIVE_REQUEST = _('There is no active request for this page and language.')
USER_NOT_ALLOWED = _('You are not allowed to approve or reject this request.')

CLOSE_FRAME = 'admin/cms/page/close_frame.html'


class ActionView(FormView):

    template_name = 'workflows/admin/action_form.html'
    form_class = ActionForm
    action_type = None
    admin_title = None
    admin_save_label = None
    confirm_message = _('Done')

    @cached_property
    def language(self):
        """
        Returns current language.

        :rtype: str
        """
        return self.args[1]

    @cached_property
    def page(self):
        """
        Returns current page which must be draft.

        :rtype: Page
        """
        pk = self.args[0]
        try:
            return Page.objects.get(
                pk=pk,
                publisher_is_draft=True,  # redundant, but ensuring we only deal with drafts
            )
        except Page.DoesNotExist:
            raise Http404

    @cached_property
    def title(self):
        """
        Returns title instance of current page/language.

        :rtype: Title
        """
        try:
            return self.page.title_set.get(language=self.language)
        except Title.DoesNotExist:
            raise Http404

    @cached_property
    def workflow(self):
        """
        Returns the appropriate workflow for the current title.

        :rtype: workflows.models.Workflow
        """
        return Workflow.get_workflow(self.title)

    @cached_property
    def user(self):
        """
        Returns the user calling the view.

        :rtype: django.contrib.auth.models.User
        """
        return self.request.user

    @cached_property
    def action_request(self):
        """
        Returns the initial request action of the current title's current action chain.

        :rtype: Action
        """
        return Action.get_current_request(self.title)

    @cached_property
    def stage(self):
        """
        Returns the workflow stage that will be associated with the action created by this view.
        That can be None in the case of the initial request which is never associated with a stage.

        :rtype: workflows.models.WorkflowStage
        """
        if not self.action_request:
            return None
        return self.action_request.get_next_stage(self.user)

    def validate(self):
        """Validates that this view can legally be called with all the current parameters.
        """
        if self.workflow is None:
            raise InvalidAction(NO_WORKFLOW)

    def get_success_url(self):
        """
        Url to redirect to after successful post.

        :rtype: str
        """
        return self.title.path

    def get_failed_url(self):
        """
        Url to redirect to after failed validation.

        :rtype: str
        """
        return self.request.META.get('HTTP_REFERER', self.get_success_url())

    def get_form_url(self):
        """
        Url to submit form to.

        :rtype: str
        """
        return self.request.path

    def dispatch(self, request, *args, **kwargs):
        try:
            self.validate()
        except InvalidAction as e:
            messages.error(request, e.message)
            return redirect(self.get_failed_url())
        return super(ActionView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Kwargs to initialize form with. The form needs some extra information
        as the actual Action creation is handled by the form's save method.

        :rtype: dict
        """
        kwargs = super(ActionView, self).get_form_kwargs()
        kwargs.update({
            'title': self.title,
            'stage': self.stage,
            'workflow': self.workflow,
            'action_type': self.action_type,
            'request': self.request,
        })
        return kwargs

    def form_valid(self, form):
        action = form.save()
        send_action_mails(action, editor=form.editor)
        messages.success(self.request, self.confirm_message)
        # context variables needed for close_frame to work
        return render(self.request, CLOSE_FRAME, {
            'opts': Action._meta,
            'root_path': reverse('admin:index'),
        })

    def get_context_data(self, **kwargs):
        """
        :rtype: dict
        """
        ctx = super(ActionView, self).get_context_data(**kwargs)
        form = ctx.get('form')
        # Admin context
        ctx.update({
            'title': self.admin_title,
            'opts': Action._meta,
            'root_path': reverse('admin:index'),
            'adminform': ctx.get('form'),
            'errors': form.errors,
            'is_popup': True,
            'form_url': self.get_form_url(),
            'save_label': self.admin_save_label
        })
        return ctx


class RequestView(ActionView):
    action_type = Action.REQUEST
    admin_title = _('Submit request for changes')
    admin_save_label = _('Submit request for changes')
    confirm_message = _('Changes successfully submitted for approval')

    def validate(self):
        super(RequestView, self).validate()
        if self.action_request and not self.action_request.is_closed():
            raise InvalidAction(ACTIVE_REQUEST)


class ApproveRejectMixinView(object):
    def validate(self):
        super(ApproveRejectMixinView, self).validate()
        if self.action_request is None:
            raise InvalidAction(NO_ACTIVE_REQUEST)
        if self.stage is None:
            raise InvalidAction(USER_NOT_ALLOWED)


class ApproveView(ApproveRejectMixinView, ActionView):
    action_type = Action.APPROVE
    admin_title = _('Approve request')
    admin_save_label = admin_title
    confirm_message = _('Request successfully approved')


class RejectView(ApproveRejectMixinView, ActionView):
    action_type = Action.REJECT
    admin_title = _('Reject request')
    admin_save_label = admin_title
    confirm_message = _('Request successfully rejected')


class CancelView(ActionView):
    action_type = Action.CANCEL
    admin_title = _('Cancel request')
    admin_save_label = admin_title
    confirm_message = _('Request successfully cancelled')


WORKFLOW_VIEWS = {
    Action.REQUEST: RequestView,
    Action.APPROVE: ApproveView,
    Action.REJECT: RejectView,
    Action.CANCEL: CancelView,
}


class InvalidAction(Exception):
    def __init__(self, message):
        self.message = message
        super(InvalidAction, self).__init__()
