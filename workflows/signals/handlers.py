# -*- coding: utf-8 -*-
from cms.operations import PUBLISH_PAGE_TRANSLATION
from django.dispatch import receiver

from cms.signals import post_obj_operation

from workflows.models import Action


# self._send_post_page_operation(
#                 request,
#                 operation=operations.PUBLISH_PAGE_TRANSLATION,
#                 token=operation_token,
#                 obj=page,
#                 translation=page.get_title_obj(language=language),
#                 successful=all_published,
#             )
#
# post_obj_operation.send(
#             sender=self.__class__,
#             operation=operation,
#             request=request,
#             token=token,
#             **kwargs
#         )

# @receiver(post_publish)  # cannot get user from this one unfortunately
@receiver(post_obj_operation)
def close_moderation_request(sender, request=None, operation=None, translation=None, successful=None, **kwargs):
    if operation != PUBLISH_PAGE_TRANSLATION:
        return

    if not successful:
        return

    current_request = Action.get_current_request(translation)

    if current_request is None:
        return

    if not current_request.is_publishable():
        raise ValueError('Page is not publishable!')

    current_action = current_request.last_action()
    current_action.add_child(
        title = translation,
        workflow=current_action.workflow,
        # stage=None,
        # group=None,
        action_type=Action.FINISH,
        user=request.user,
        message=''
    )



# request = kwargs['request']
#     operation_type = kwargs['operation']
#     is_publish = operation_type == PUBLISH_PAGE_TRANSLATION
#     publish_successful = kwargs.get('successful')
#
#     if not is_publish or not publish_successful:
#         return
#
#     page = kwargs['obj']
#     translation = kwargs['translation']
#
#     workflow = get_page_moderation_workflow(page)
#
#     if not workflow:
#         return
#
#     active_request = workflow.get_active_request(page, translation.language)
#
#     if not active_request:
#         return
#
#     active_request.update_status(
#         action=ACTION_FINISHED,
#         by_user=request.user,
#     )

