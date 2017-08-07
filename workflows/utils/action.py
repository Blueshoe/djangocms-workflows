# -*- coding: utf-8 -*-
from cms.models import Title
from ..models import Action


def get_name(user, default=None):
    try:
        return user.get_full_name()
    except AttributeError:
        try:
            return user.get_username()
        except AttributeError:
            return default or str(user)


def get_current_action(title):
    """
    :type title: Title
    :param title:
    :return:
    """
    # TODO check logic
    try:
        latest_request = Action.objects.filter(title=title, depth=1).latest('created')
    except Action.DoesNotExist:
        return None

    return latest_request.get_tree().latest('depth')
