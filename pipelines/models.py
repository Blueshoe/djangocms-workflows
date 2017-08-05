# -*- coding: utf-8 -*-
from cms.extensions.models import TitleExtension
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from treebeard.mp_tree import MP_Node


class Pipeline(models.Model):
    name = models.CharField(
        _('Name'),
        max_length=63,
        unique=True,
        help_text=_('Please provide a descriptive name!')
    )

    default = models.BooleanField(
        _('Default pipeline'),
        default=False,
        help_text=_('Should this be the default pipeline for all pages?')
    )

    class Meta:
        verbose_name = _('Pipeline')
        verbose_name_plural = _('Pipelines')


class PipelineStage(models.Model):
    pipeline = models.ForeignKey(
        'pipelines.Pipeline',
        on_delete=models.CASCADE,
        verbose_name=_('Pipeline'),
        related_name='stages'
    )

    group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name=_('Group'),
        help_text=_('Only members of this group can approve this pipeline stage.'),
    )

    # admin-sortable required
    order = models.PositiveSmallIntegerField(
        _('Order'),
        default=0
    )

    optional = models.BooleanField(
        _('Optional'),
        default=False,
        help_text=_('Is this pipeline stage optional?')
    )

    class Meta:
        verbose_name = _('Pipeline stage')
        verbose_name_plural = _('Pipelines stages')
        ordering = ('order',)
        unique_together = (('pipeline', 'group'),)


class TitlePipeline(TitleExtension):
    pipeline = models.ForeignKey(
        'pipelines.Pipeline',
        on_delete=models.CASCADE,
        verbose_name=_('Pipeline'),
        help_text=_('The pipeline set here is language specific.')
    )

    class Meta:
        verbose_name = _('Title pipeline')
        verbose_name_plural = _('Title pipelines')


class Action(MP_Node):
    """

    """
    OPEN, APPROVE, REJECT, CANCEL, FINISH = 'open', 'approve', 'reject', 'cancel', 'finish'

    TYPES = (
        (OPEN, _('open')),
        (APPROVE, _('approve')),
        (REJECT, _('reject')),
        (CANCEL, _('cancel')),
        (FINISH, _('finish')),
    )

    title = models.ForeignKey(
        'cms.Title',
        on_delete=models.CASCADE,
        verbose_name=_('Title')
    )

    stage = models.ForeignKey(
        'pipelines.PipelineStage',
        on_delete=models.SET_NULL,
        verbose_name=_('Stage'),
        # allow null for open action and if Stage is deleted on Pipeline
        null=True,
    )

    # persist stage Group in case stage is deleted
    group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name=_('Group'),
    )

    action_type = models.CharField(
        _('Action type'),
        max_length=10,
        choices=TYPES,
        default=OPEN,
    )

    created = models.DateTimeField(
        _('Created'),
        auto_now_add=True,
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        verbose_name=_('User'),
        null=True
    )

    message = models.TextField(
        _('Message'),
        help_text=_('Provide more information!')
    )

    class Meta:
        verbose_name = _('Pipeline action')
        verbose_name_plural = _('Pipeline actions')
        unique_together = (('title', 'stage'),)

