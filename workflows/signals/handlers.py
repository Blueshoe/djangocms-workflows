# -*- coding: utf-8 -*-
from cms.operations import PUBLISH_PAGE_TRANSLATION
from django.dispatch import receiver

from cms.signals import post_obj_operation

from ..models import Action


# @receiver(post_publish)  # cannot easily get user from this signal unfortunately
@receiver(post_obj_operation)
def close_moderation_request(sender, request=None, operation=None, translation=None, successful=None, **kwargs):
    current_request = Action.get_current_request(translation)

    if all((operation == PUBLISH_PAGE_TRANSLATION, successful, current_request)):
        if not current_request.is_publishable():
            raise ValueError('Page is not publishable!')

        current_action = current_request.last_action()
        current_request.last_action().add_child(
            title=translation,
            workflow=current_action.workflow,
            action_type=Action.PUBLISH,
            user=request.user,
            message=''
        )
