# -*- coding: utf-8 -*-
from cms.utils.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from cms.models import Title

from .action import get_name
from ..models import Action


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

    :param action: Action triggering mails
    :type action: Action
    :type editor: django.contrib.auth.models.AbstractUser
    :return: # TODO
    :rtype: # TODO
    """
    # TODO
    # open:
    #   - request mail to first editor
    # approve:
    #   - approve mail to author
    #   - request mail to next editor
    # reject:
    #   - reject mail to author
    # cancel:
    #   - cancel mail to author
    sent = False

    if action.action_type not in SUBJECTS:
        return sent
    subjects = SUBJECTS[action.action_type]
    context = _context(action)

    if AUTHOR in subjects:
        subject = subjects[AUTHOR].__format__(**context)
        txt_template = 'workflows/emails/author_{}.txt'.format(action.action_type)
        to = [action.get_author().email]
        send_mail(subject, txt_template, to, context=context)
        sent = True

    if EDITOR in subjects:
        subject = subjects[EDITOR].__format__(**context)
        to = get_editor_to(action, editor=editor)
        if to:
            txt_template = 'workflows/emails/editor_{}.txt'.format(action.action_type)
            send_mail(subject, txt_template, to, context=context)
            sent = True

    return sent


def _context(action):
    author = action.get_author()
    editor = action.user
    context = {
        # 'page': title.page,
        # 'language': title.language,
        'url': get_absolute_url(action.title),
        'author_name': get_name(author, default=_('author')),
        'editor_name': get_name(editor, default=_('editor')),
        'message': action.message,
        'project': getattr(settings, 'PROJECT_NAME', 'djangocms-workflows')
    }
    return context


def get_editor_to(action, editor=None):
    """
    :type editor: django.contrib.auth.models.AbstractUser
    :param editor:
    :return:
    """
    if editor:
        return [editor.email]
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

