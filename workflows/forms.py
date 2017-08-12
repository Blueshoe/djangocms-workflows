# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from workflows.utils.action import get_current_action
from .models import Action
from .utils.workflow import get_workflow


# TODO form for Workflow admin (esp. Formset for Stage inlines)


class ActionForm(forms.ModelForm):
    message = forms.CharField(
        label=_('Message'),
        required=False,
        widget=forms.Textarea()
    )

    class Meta:
        model = Action
        fields = ('message',)

    def __init__(self, *args, **kwargs):
        self.stage = kwargs.pop('stage', None)
        self.action_type = kwargs.pop('action_type')  # {open, approve, reject, cancel}
        self.title = kwargs.pop('title')
        self.current_action = get_current_action(self.title)
        self.workflow = get_workflow(self.title)
        self.request = kwargs.pop('request')
        self.user = self.request.user
        super(ActionForm, self).__init__(*args, **kwargs)

        if 'moderator' in self.fields:
            self.configure_moderator_field()

    def get_moderator(self):
        return self.cleaned_data.get('moderator')

    def configure_moderator_field(self):
        next_role = self.workflow.first_step.role
        users = next_role.get_users_queryset().exclude(pk=self.user.pk)
        self.fields['moderator'].empty_label = ugettext('Any {role}').format(role=next_role.name)
        self.fields['moderator'].queryset = users

    def save(self):
        # TODO
        # title -> self.title
        # workflow -> self.workflow
        # stage -> self.stage
        # group -> stage.group
        # action_type -> self.action_type
        # created -> auto
        # user -> self.user
        # message -> ...
        return None
