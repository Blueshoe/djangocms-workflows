# -*- coding: utf-8 -*-
import logging

from cms.models import Title

from ..models import WorkflowExtension, Workflow, Action

logger = logging.getLogger('django.cms-workflows')


def get_workflow(title):
    """Returns appropriate workflow for this title.

    :type title: Title
    :rtype: Workflow | None
    :raises: Workflow.MultipleObjectsReturned
    """
    # 1. check for custom workflow
    try:
        return title.workflowextension.workflow
    except WorkflowExtension.DoesNotExist:
        pass

    # 2. check for inherited workflow up the site tree
    titles = Title.objects.filter(page__in=title.page.get_ancestors())  # all title of ancestor pages ...
    titles = titles.filter(language=title.language)                     # and same language ...
    titles = titles.filter(workflowextension__descendants=True)         # that have an inherited workflow ...
    titles = titles.order_by('-page__depth')                            # bottom up
    ancestor_title = titles.first()

    if ancestor_title:
        return ancestor_title.workflowextension.workflow

    try:
        # 3. check for default workflow
        return Workflow.default_workflow()
    except Workflow.DoesNotExist:
        # 4. no workflow applies
        return None
    except Workflow.MultipleObjectsReturned:
        logger.warning('Multiple default workflows set. This should not happen!')
        raise


def get_current_request(title):
    workflow = get_workflow(title)
    if workflow is None:
        return None
    try:
        # there can only be one open request per title at a time and it must be the last
        return Action.get_root_nodes().filter(title=title).latest('created')
    except Action.DoesNotExist:
        return None
