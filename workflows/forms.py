# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from workflows.utils.action import get_current_action
from workflows.utils.email import send_action_mails
from .models import Action


# TODO form for Workflow admin (esp. Formset for Stage inlines)


class ActionForm(forms.Form):
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

    def __init__(self, *args, **kwargs):
        self.stage = kwargs.pop('stage', None)
        self.title = kwargs.pop('title')
        self.request = kwargs.pop('request')
        self.workflow = kwargs.pop('workflow')
        self.action_type = kwargs.pop('action_type')  # {open, approve, reject, cancel}
        self.next_stage = self.workflow.next_mandatory_stage(self.stage)
        self.group = getattr(self.stage, 'group', None)
        self.current_action = get_current_action(self.title)
        self.user = self.request.user
        super(ActionForm, self).__init__(*args, **kwargs)
        self.adjust_editor()

    @property
    def editor(self):
        """
        :rtype: django.contrib.auth.models.User
        """
        return self.cleaned_data.get('editor')

    @property
    def editors(self):
        if self.next_stage is None:
            raise ValueError('No next stage!')
        if self.editor:
            return get_user_model().objects.filter(pk=self.editor.pk)
        return self.next_stage.group.user_set.all()

    @property
    def message(self):
        """
        :rtype: str
        """
        return self.cleaned_data.get('message', '')

    def adjust_editor(self):
        if self.action_type in (Action.CANCEL, Action.REJECT) or self.next_stage is None:
            self.fields.pop('editor', None)  # no editor can be chosen
            return
        group = self.next_stage.group
        self.fields['editor'].queryset = group.user_set.all()
        self.fields['editor'].empty_label = _('Any {}').format(group.name)

    def save(self):
        """
        :rtype: Action
        """
        self.current_action = Action()
        init_kwargs = {
            attr: getattr(self, attr) for attr in
            ('message', 'user', 'title', 'workflow', 'stage', 'action_type', 'group')
        }
        if self.current_action is None:
            assert self.action_type == Action.REQUEST  # root must be request
            return Action.add_root(**init_kwargs)
        else:
            assert self.action_type != Action.REQUEST  # non-root must not be request
            return self.current_action.add_child(**init_kwargs)
