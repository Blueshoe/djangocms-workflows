# -*- coding: utf-8 -*-
from django.conf import settings
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
    pass


def _context(action):
    author = action.get_author()
    editor = action.user
    context = {
        # 'page': title.page,
        # 'language': title.language,
        'url': get_absolute_url(action.title),
        'author_name': get_name(author, default=_('author')),
        'editor_name': get_name(editor, default=_('editor')),
        'project': getattr(settings, 'PROJECT_NAME', 'djangocms-workflows')
    }
    return context


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

