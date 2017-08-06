# -*- coding: utf-8 -*-
import logging

from cms.models import Title

from ..models import TitlePipeline, Pipeline


logger = logging.getLogger('django.cms-pipelines')


def get_pipeline(title):
    """Returns appropriate pipeline for this title.

    :type title: Title
    :rtype: Pipeline | None
    :raises: Pipeline.MultipleObjectsReturned
    """
    # check for custom pipeline
    try:
        return title.titlepipeline
    except TitlePipeline.DoesNotExist:
        pass

    # check for default pipeline
    try:
        return Pipeline.default_pipeline()
    except Pipeline.DoesNotExist:
        return None
    except Pipeline.MultipleObjectsReturned:
        logger.warning('Multiple default pipelines set. This should not happen!')
        raise
