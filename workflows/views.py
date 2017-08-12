# -*- coding: utf-8 -*-
from cms.models import Page, Title
from django.http import Http404
from django.shortcuts import render

# Create your views here.
# TODO Views handling action creation
from django.utils.functional import cached_property
from django.views.generic.edit import FormView

from workflows.utils.workflow import get_workflow, get_current_request


class ActionView(FormView):
    action_type = None

    # def dispatch(self, request, *args, **kwargs):
    #     return super(ActionView, self).dispatch(request, *args, **kwargs)

    @cached_property
    def language(self):
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
        try:
            return self.page.title_set.get(language=self.language)
        except Title.DoesNotExist:
            raise Http404

    @cached_property
    def workflow(self):
        return get_workflow(self.title)

    @cached_property
    def user(self):
        return self.request.user

    @cached_property
    def action_request(self):
        return get_current_request(self.title)
