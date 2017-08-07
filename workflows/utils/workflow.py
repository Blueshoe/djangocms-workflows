# -*- coding: utf-8 -*-
import logging

from cms.models import Title

from ..models import WorkflowExtension, Workflow


logger = logging.getLogger('django.cms-workflows')


def get_workflow(title):
    """Returns appropriate workflow for this title.

    :type title: Title
    :rtype: Workflow | None
    :raises: Workflow.MultipleObjectsReturned
    """
    # check for custom workflow
    try:
        return title.workflowextension
    except WorkflowExtension.DoesNotExist:
        pass
    # TODO check for for custom workflow on ancestor pages that apply to descendants

    # check for default workflow
    try:
        return Workflow.default_workflow()
    except Workflow.DoesNotExist:
        return None
    except Workflow.MultipleObjectsReturned:
        logger.warning('Multiple default workflows set. This should not happen!')
        raise
