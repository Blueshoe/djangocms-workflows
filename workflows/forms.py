# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
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

    editor = forms.ModelChoiceField(
        label=_('Editor'),
        queryset=get_user_model().objects.none(),
        required=False
    )

    class Meta:
        model = Action
        fields = ('message',)

    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop('title')
        self.workflow = kwargs.pop('workflow')
        self.stage = kwargs.pop('stage', None)
        self.action_type = kwargs.pop('action_type')  # {open, approve, reject, cancel}
        self.current_action = get_current_action(self.title)
        self.request = kwargs.pop('request')
        self.user = self.request.user
        super(ActionForm, self).__init__(*args, **kwargs)
        self.adjust_editor()

    @property
    def editor(self):
        return self.cleaned_data.get('editor')

    def adjust_editor(self):
        next_stage = self.workflow.next_mandatory_stage(self.stage)
        if self.action_type in (Action.CANCEL, Action.REJECT) or next_stage is None:
            self.fields.pop('editor', None)  # no editor can be chosen
            return
        group = next_stage.group
        self.fields['editor'].queryset = group.user_set.all()
        self.fields['editor'].empty_label = _('Any {}').format(group.name)

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
