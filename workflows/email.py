# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cms.utils.mail import send_mail
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from cms.models import Title

from workflows.models import Action


EDITOR, AUTHOR = 'editor', 'author'

SUBJECTS = {
    Action.REQUEST: {
        EDITOR: _('{project}: Change review requested')
    },
    Action.APPROVE: {
        EDITOR: _('{project}: Change review requested'),
        AUTHOR: _('{project}: Changes approved'),
    },
    Action.REJECT: {
        AUTHOR: _('{project}: Changes rejected'),
    },
    Action.CANCEL: {
        AUTHOR: _('{project}: Changes cancelled'),
    },
}


def send_action_mails(action, editor=None):
    """
    Returns `True` if any email has been sent.

    :param action: Action triggering mails
    :type action: Action
    :type editor: django.contrib.auth.models.AbstractUser
    :rtype: bool
    """
    sent = False

    if action.action_type not in SUBJECTS:
        return sent
    subjects = SUBJECTS[action.action_type]
    context = _context(action)

    if AUTHOR in subjects:
        subject = subjects[AUTHOR].format(**context)
        txt_template = 'workflows/emails/author_{}.txt'.format(action.action_type)
        to = get_to(action, to_user=action.get_author())
        send_mail(subject, txt_template, to, context=context)
        sent = True

    if EDITOR in subjects:
        subject = subjects[EDITOR].format(**context)
        to = get_to(action, to_user=editor)
        if to:
            txt_template = 'workflows/emails/editor_{}.txt'.format(action.action_type)
            send_mail(subject, txt_template, to, context=context)
            sent = True

    return sent


def _context(action):
    author = action.get_author()
    editor = action.user
    context = {
        'url': get_absolute_url(action.title),
        'author_name': get_name(author, default=_('author')),
        'editor_name': get_name(editor, default=_('editor')),
        'message': action.message,
        'project': getattr(settings, 'PROJECT_NAME', 'djangocms-workflows')
    }
    return context


def get_to(action, to_user=None):
    """
    :type to_user: django.contrib.auth.models.AbstractUser
    :param to_user:
    :return:
    """
    if to_user:
        return [to_user.email]
    return [user.email for user in action.next_mandatory_stage_editors()]


def get_absolute_url(title):
    """
    :type title: Title
    :param title:
    :return:
    """
    scheme = ['http', 'https'][getattr(settings, 'USE_HTTPS', False)]
    domain = title.page.site.domain
    path = title.page.get_absolute_url(language=title.language).lstrip('/')
    return '{}://{}/{}'.format(scheme, domain, path)


def get_name(user, default=None):
    try:
        name = user.get_full_name()
        assert name.strip() != ''
        return name
    except (AttributeError, AssertionError):
        try:
            return user.get_username()
        except AttributeError:
            return default or str(user)
