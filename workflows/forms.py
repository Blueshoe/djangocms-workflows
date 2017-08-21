# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from .models import Action


class ActionForm(forms.Form):
    message_ = forms.CharField(
        label=_('Message'),
        required=False,
        help_text=_('You may provide some more information.'),
        widget=forms.Textarea
    )

    editor_ = forms.ModelChoiceField(
        label=_('Editor'),
        queryset=get_user_model().objects.none(),
        help_text=_('Only notify a specific user?'),
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
        cr = Action.get_current_request(self.title)
        self.current_action = None if (not cr or cr.is_closed()) else cr.last_action()
        self.user = self.request.user
        super(ActionForm, self).__init__(*args, **kwargs)
        self.adjust_editor()

    @property
    def message(self):
        """
        :rtype: str
        """
        return self.cleaned_data.get('message_', '')

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

    def adjust_editor(self):
        if self.action_type in (Action.CANCEL, Action.REJECT) or self.next_stage is None:
            self.fields.pop('editor_', None)  # no editor can be chosen
            return
        group = self.next_stage.group
        self.fields['editor_'].queryset = group.user_set.all()
        self.fields['editor_'].empty_label = _('Any {}').format(group.name)

    def save(self):
        """
        :rtype: Action
        """
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
