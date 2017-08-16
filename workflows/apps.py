# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WorkflowsConfig(AppConfig):
    name = 'workflows'
    verbose_name = _('Django CMS Workflows')

    def ready(self):
        # needed to connect signal handlers
        from workflows.signals import handlers
