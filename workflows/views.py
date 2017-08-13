# -*- coding: utf-8 -*-
from cms.models import Page, Title
from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _

# Create your views here.
# TODO Views handling action creation
from django.utils.functional import cached_property
from django.views.generic.edit import FormView

from workflows.models import Action
from workflows.utils.workflow import get_workflow, get_current_request


NO_WORKFLOW = _('')  # TODO
ACTIVE_REQUEST = _('')
NO_ACTIVE_REQUEST = _('')
USER_NOT_ALLOWED = _('')


class ActionView(FormView):
    action_type = None

    # def dispatch(self, request, *args, **kwargs):
    #     return super(ActionView, self).dispatch(request, *args, **kwargs)

    @cached_property
    def language(self):
        """
        :rtype: str
        """
        return self.kwargs['language']

    @cached_property
    def page(self):
        """
        :rtype: Page
        """
        pk = self.kwargs['paged_id']
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
        :rtype: Title
        """
        try:
            return self.page.title_set.get(language=self.language)
        except Title.DoesNotExist:
            raise Http404

    @cached_property
    def workflow(self):
        """
        :rtype: workflows.models.Workflow
        """
        return get_workflow(self.title)

    @cached_property
    def user(self):
        """
        :rtype: django.contrib.auth.models.User
        """
        return self.request.user

    @cached_property
    def action_request(self):
        """
        :rtype: Action
        """
        return get_current_request(self.title)

    @cached_property
    def stage(self):
        """
        :rtype: workflows.models.WorkflowStage
        """
        if not self.action_request:
            return None
        return self.action_request.get_next_stage(self.user)

    def validate(self):
        if self.workflow is None:
            raise InvalidAction(NO_WORKFLOW)

    def get_success_url(self):
        return self.title.path

    def get_failed_url(self):
        return self.request.META.get('HTTP_REFERER', self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        try:
            self.validate()
        except InvalidAction as e:
            messages.error(request, e.message)
            return redirect(self.get_failed_url())
        return super(ActionView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ActionView, self).get_form_kwargs()
        kwargs.update({
            'title': self.title,
            'stage': self.stage,
            'workflow': self.workflow,
            'action_type': self.action_type,
            'request': self.request,
        })
        return kwargs


class RequestView(ActionView):
    action_type = Action.REQUEST

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


class RejectView(ApproveRejectMixinView, ActionView):
    action_type = Action.REJECT


class CancelView(ActionView):
    action_type = Action.CANCEL


class InvalidAction(Exception):
    def __init__(self, message):
        self.message = message
        super(InvalidAction, self).__init__()
