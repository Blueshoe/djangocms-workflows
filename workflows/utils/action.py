# -*- coding: utf-8 -*-
from cms.models import Title

from .workflow import get_workflow
from ..models import Action


def get_name(user, default=None):
    try:
        return user.get_full_name()
    except AttributeError:
        try:
            return user.get_username()
        except AttributeError:
            return default or str(user)


def get_current_request(title):
    """
    :rtype: Action
    """
    workflow = get_workflow(title)
    if workflow is None:
        return None
    try:
        # there can only be one open request per title at a time and it must be the last
        return Action.get_root_nodes().filter(title=title).latest('created')
    except Action.DoesNotExist:
        return None


def get_current_action(title):
    """
    :type title: Title
    :param title:
    :rtype: Action
    """
    latest_request = get_current_request(title)
    if latest_request:
        return latest_request.get_descendants().latest('depth')
    return None


def is_editable(title):
    """
    :rtype: bool
    """
    current_request = get_current_request(title)
    if current_request is None:
        return True
    return current_request.is_closed()
