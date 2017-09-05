# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from cms.extensions.extension_pool import extension_pool
from cms.extensions.models import TitleExtension
from cms.models import Title
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from treebeard.mp_tree import MP_Node

logger = logging.getLogger('django.cms-workflows')


class Workflow(models.Model):
    """
    Model representing a editorial workflow. A workflow is simply a sequence of ordered
    mandatory or optional stages. Every `cms.Title` instance can be associated with a
    concrete Workflow instance via the WorkflowExtension. At most one workflow can be
    made the default workflow which is assumed for all titles without their own or
    inherited workflow.
    """
    name = models.CharField(
        _('Name'),
        max_length=63,
        unique=True,
        help_text=_('Please provide a descriptive name!')
    )

    default = models.BooleanField(
        _('Default workflow'),
        default=False,
        help_text=_('Should this be the default workflow for all pages and languages?')
    )

    class Meta:
        verbose_name = _('Workflow')
        verbose_name_plural = _('Workflows')

    def save(self, **kwargs):
        if self.default:
            Workflow.objects.filter(default=True).exclude(pk=self.pk).update(default=False)
        super(Workflow, self).save(**kwargs)

    def __str__(self):
        return self.name

    @classmethod
    def default_workflow(cls):
        """
        :return: The default workflow if one exists, else `None`
        """
        try:
            return cls.objects.get(default=True)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            logger.error('Multiple default workflows set. This should not happen!')
            raise

    @classmethod
    def get_workflow(cls, title):
        """Returns appropriate workflow for this title.

        :type title: Title
        :rtype: Workflow | None
        :raises: Workflow.MultipleObjectsReturned
        """
        if title is None:
            return cls.default_workflow()
        # 1. check for custom workflow
        try:
            return title.workflowextension.workflow
        except WorkflowExtension.DoesNotExist:
            pass

        # 2. check for inherited workflow up the site tree
        titles = Title.objects.filter(page__in=title.page.get_ancestors())  # all title of ancestor pages ...
        titles = titles.filter(language=title.language)  # and same language ...
        titles = titles.filter(workflowextension__descendants=True)  # that have an inherited workflow ...
        titles = titles.order_by('-page__depth')  # bottom up
        ancestor_title = titles.first()

        if ancestor_title:
            return ancestor_title.workflowextension.workflow

        # 3. check for default workflow, might be None
        return cls.default_workflow()

    @cached_property
    def mandatory_stages(self):
        return self.stages.filter(optional=False)

    @cached_property
    def first_mandatory_stage(self):
        return self.mandatory_stages.first()

    def possible_next_stages(self, stage=None):
        """
        Return a queryset of all possible stages that can be used for the next action. These
        are all stages starting with the very next stage up to and including the next mandatory
        stage.
        """
        if stage:
            return stage.possible_next_stages
        fms = self.first_mandatory_stage
        return self.stages.filter(order__lte=fms.order)

    def next_mandatory_stage(self, stage=None):
        if stage is None:
            return self.first_mandatory_stage
        return self.mandatory_stages.filter(order__gt=stage.order).first()


class WorkflowStage(models.Model):
    """
    Represents a stage of a workflow. It is associated with a group. That means only a member of the
    group can approve or reject the stage.
    """
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        verbose_name=_('Workflow'),
        related_name='stages'
    )

    group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name=_('Group'),
        help_text=_('Only members of this group can approve this workflow stage.'),
    )

    # admin-sortable required
    order = models.PositiveSmallIntegerField(
        _('Order'),
        default=0
    )

    optional = models.BooleanField(
        _('Optional'),
        default=False,
        help_text=_('Is this workflow stage optional?')
    )

    class Meta:
        verbose_name = _('Workflow stage')
        verbose_name_plural = _('Workflow stages')
        ordering = ('order',)
        unique_together = (('workflow', 'group'),)

    def __str__(self):
        return self.group.name + ('[optional]' if self.optional else '')

    @cached_property
    def next_mandatory_stage(self):
        return self.workflow.stages.filter(order__gt=self.order, optional=False).first()

    @cached_property
    def possible_next_stages(self):
        nms = self.next_mandatory_stage
        pending = self.workflow.stages.filter(order__gt=self.order)
        if nms is not None:
            pending = pending.filter(order__lte=nms.order)
        return pending


class WorkflowExtension(TitleExtension):
    """
    This extension holds the workflow association of a cms.Title instance.
    """
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        verbose_name=_('Workflow'),
        help_text=_('The workflow set here is language specific.')
    )

    descendants = models.BooleanField(
        _('Descendants'),
        help_text=_('Should this workflow apply to descendant pages?'),
        default=True
    )

    class Meta:
        verbose_name = _('Workflow extension')
        verbose_name_plural = _('Workflow extensions')

    def __str__(self):
        return '{title} ({lang}): {workflow}'.format(
            title=self.extended_object.title,
            lang=self.extended_object.language,
            workflow=self.workflow
        )

    @cached_property
    def language(self):
        return self.extended_object.language


extension_pool.register(WorkflowExtension)


class Action(MP_Node):
    """
    Actions are the instantiations of workflow stages. They model a concrete editorial process that
    is modelled as a linked sequence (a 'unary' tree) using treebeard's MP_Node:

    The initial submission request is always a root node of action_type REQUEST.
    This is followed by n actions of type APPROVE each of which is associated with a stage of the
    appropriate workflow.
    The last action in such a chain is an action of either of REJECT, CANCEL, or PUBLISH.
    CANCEL/PUBLISH actions are not associated with a stage, but REJECT is.

    E.g.:

    workflow: editor1 [-> editor2] -> test_user    (editor2 is optional)

        action: stage/group
    ==========:============
    1. REQUEST: --
    2. APPROVE: editor1
    3. APPROVE: editor2
    4. APPROVE: test_user
    5. PUBLISH: --

    1. REQUEST: --
    2. APPROVE: editor1
    3. APPROVE: test_user
    4. PUBLISH: --

    1. REQUEST: --
    2. APPROVE: editor1
    3.  REJECT: test_user

    1. REQUEST: --
    2. APPROVE: editor1
    3.  CANCEL: --
    """
    REQUEST, APPROVE, REJECT, CANCEL, PUBLISH, DIFF = 'request', 'approve', 'reject', 'cancel', 'publish', 'diff'
    TYPES = (
        (REQUEST, _('request')),
        (APPROVE, _('approve')),
        (REJECT, _('reject')),
        (CANCEL, _('cancel')),
        (PUBLISH, _('publish')),
        (DIFF, _('diff')),
    )

    REQUESTED, APPROVED, REJECTED, CANCELLED, PUBLISHED = 'requested', 'approved', 'rejected', 'cancelled', 'published'
    STATUS = (
        (REQUESTED, _('Requested')),
        (APPROVED, _('Approved')),
        (REJECTED, _('Rejected')),
        (CANCELLED, _('Cancelled')),
        (PUBLISHED, _('Published')),
    )

    title = models.ForeignKey(
        'cms.Title',
        on_delete=models.CASCADE,
        verbose_name=_('Title'),
    )

    # persist workflow in case the workflow changes on the title
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        verbose_name=_('Workflow'),
    )

    stage = models.ForeignKey(
        'workflows.WorkflowStage',
        on_delete=models.SET_NULL,
        verbose_name=_('Stage'),
        # allow null for open action and if Stage is deleted on Workflow
        null=True,
        default=None,
    )

    # persist stage Group in case stage is deleted
    group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name=_('Group'),
        null=True,
        default=None
    )

    action_type = models.CharField(
        _('Action type'),
        max_length=10,
        choices=TYPES,
        default=REQUEST,
    )

    created = models.DateTimeField(
        _('Created'),
        auto_now_add=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        verbose_name=_('User'),
        null=True
    )

    message = models.TextField(
        _('Message'),
    )

    class Meta:
        verbose_name = _('Workflow action')
        verbose_name_plural = _('Workflow actions')
        ordering = ('depth', 'created')

    def __str__(self):
        return '#{}: {}'.format(self.title_id, self.action_type)

    def save(self, **kwargs):
        if self.action_type == self.REQUEST:
            try:
                previous = Action.get_requests(title=self.title).exclude(pk=self.pk).latest('created')
            except Action.DoesNotExist:
                pass
            else:
                assert previous.is_closed(), 'Close previous request #{pk} before new request'.format(pk=previous.pk)
        super(Action, self).save(**kwargs)

    def is_closed(self):
        return self.last_action().action_type in (self.REJECT, self.CANCEL, self.PUBLISH)

    def get_request(self):
        """Root of this chain of actions.

        :rtype: Action
        :return:
        """
        return self.get_root()

    def get_author(self):
        """Return author of changes.

        :rtype: django.contrib.auth.models.AbstractUser
        :return: author of changes
        """
        return self.get_request().user

    def next_mandatory_stage(self):
        """
        :rtype: WorkflowStage
        :return:
        """
        if self.action_type == self.REQUEST:
            return self.workflow.first_mandatory_stage
        if self.action_type == self.APPROVE and self.stage:
            return self.stage.next_mandatory_stage
        return None

    def next_mandatory_stage_editors(self):
        nms = self.next_mandatory_stage()
        if not nms:
            return get_user_model().objects.none()
        return nms.group.user_set.all()

    def possible_next_stages(self):
        return self.workflow.possible_next_stages(self.stage)

    def last_action(self):
        """
        Returns the latest action of this action's action chain.

        :rtype: Action
        """
        return Action.get_tree(parent=self).latest('depth')

    def is_publishable(self):
        """
        Is this action's title publishable with regard to this action's action chain?

        :rtype: bool
        """
        if self.is_closed():  # rejected, cancelled, or already published?
            return False
        last_action = self.last_action()
        if last_action.action_type != self.APPROVE:
            return False
        return last_action.next_mandatory_stage() is None

    def get_next_stage(self, user):
        if self.is_closed():
            return None
        return self.possible_next_stages().filter(group__user=user).last()

    @cached_property
    def status(self):
        la = self.last_action()
        if la.action_type == self.CANCEL:
            return self.CANCELLED
        if la.action_type == self.PUBLISH:
            return self.PUBLISHED
        if la.action_type == self.REJECT:
            return self.REJECTED
        if self.is_publishable():
            return self.APPROVED
        else:
            return self.REQUESTED

    @cached_property
    def status_display(self):
        return dict(self.STATUS)[self.status]
    status_display.short_description = _('Status')

    @classmethod
    def get_requests(cls, title=None):
        requests = cls.get_root_nodes()
        if title:
            requests = requests.filter(title=title)
        return requests

    @classmethod
    def get_current_request(cls, title):
        """
        Returns the most recent request (root action) for this title.

        :rtype: Action
        """
        workflow = Workflow.get_workflow(title)
        if workflow is None:
            return None
        try:
            # there can only be one open request per title at a time and it must be the last
            return cls.get_requests(title=title).latest('created')
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_current_action(cls, title):
        """
        Returns the most recent action for this title.

        :type title: Title
        :param title:
        :rtype: Action
        """
        latest_request = cls.get_current_request(title)
        if latest_request:
            return cls.get_tree(parent=latest_request).latest('depth')
        return None

    @classmethod
    def is_editable(cls, title):
        """
        Can this title be edited at the moment?
        Only returns `True` if there is no open request at the moment.
        :type title: Title
        :rtype: bool
        """
        if not title.publisher_is_draft:
            return False
        current_request = cls.get_current_request(title)
        if current_request is None:
            return True
        return current_request.is_closed()

    @classmethod
    def requiring_action(cls, user):
        """
        Returns a list of all actions that currently require approve or reject activity
        by this user.

        :type user: django.contrib.auth.models.User
        :rtype: list
        """
        actions = []
        for title in Title.objects.filter(action__isnull=False).distinct():
            ca = cls.get_current_action(title)
            if user in ca.next_mandatory_stage_editors():
                actions.append(ca)
        return actions
