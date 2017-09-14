# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cms.cms_toolbars import PlaceholderToolbar, PageToolbar, PAGE_MENU_IDENTIFIER
from cms.toolbar.items import ModalButton, Dropdown, DropdownToggleButton, SideframeButton, BaseItem, ButtonList
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.extensions.toolbar import ExtensionToolbar
from cms.utils.urlutils import admin_reverse
from cms.utils import get_language_list  # needed to get the page's languages
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from .models import Action, Workflow, WorkflowExtension


def get_placeholder_toolbar():
    try:
        return toolbar_pool.toolbars.pop('cms.cms_toolbars.PlaceholderToolbar')
    except KeyError:
        return PlaceholderToolbar


def get_page_toolbar():
    try:
        return toolbar_pool.toolbars.pop('cms.cms_toolbars.PageToolbar')
    except KeyError:
        return PageToolbar


class WorkflowExtensionToolbar(ExtensionToolbar):
    # As described in the docs
    model = WorkflowExtension

    def populate(self):
        # setup the extension toolbar with permissions and sanity checks
        current_page_menu = self._setup_extension_toolbar()

        # if it's all ok
        if current_page_menu and self.toolbar.edit_mode:
            # create a sub menu labelled "Workflows" at position 1 in the menu
            sub_menu = self._get_sub_menu(
                current_page_menu, 'submenu_label', _('Workflow'), position=1
            )

            # retrieves the instances of the current title extension (if any) and the toolbar item URL
            urls = self.get_title_extension_admin()

            # we now also need to get the title set (i.e. different language titles) for this page
            page = self._get_page()
            titles = page.title_set.filter(language__in=get_language_list(page.site_id))

            # cycle through the list
            for (title_extension, url), title in zip(urls, titles):

                # adds toolbar items
                sub_menu.add_modal_item(
                    _('for "{title}" ({lang})').format(title=title.title, lang=title.language),
                    url=url,
                    disabled=not self.toolbar.edit_mode
                )


class WorkflowPlaceholderToolbar(get_placeholder_toolbar()):
    def __init__(self, *args, **kwargs):
        super(WorkflowPlaceholderToolbar, self).__init__(*args, **kwargs)
        self.editable = True

    def init_from_request(self):
        super(WorkflowPlaceholderToolbar, self).init_from_request()
        if self.page:
            self.editable = Action.is_editable(self.page.title_set.filter(language=self.current_lang).first())
            self.toolbar.content_renderer._placeholders_are_editable &= self.editable

    def add_structure_mode(self):
        if self.editable:
            return super(WorkflowPlaceholderToolbar, self).add_structure_mode()


# class WorkflowPageToolbar(get_page_toolbar()):
class WorkflowPageToolbar(PageToolbar):
    WORKFLOW_URL_NAME = 'workflow_{}'
    BUTTON_NAMES = {
        Action.REQUEST: _('Request approval for changes'),
        Action.APPROVE: _('Approve changes'),
        Action.REJECT: _('Reject changes'),
        Action.CANCEL: _('Cancel request'),
        Action.DIFF: _('Diff view'),
    }
    current_request = None

    def add_page_menu(self):
        if not self.editable or self.in_app:
            self.toolbar.get_or_create_menu(
                PAGE_MENU_IDENTIFIER, _('Page'), position=1, disabled=True
            )
        else:
            super(WorkflowPageToolbar, self).add_page_menu()

    def init_from_request(self):
        super(WorkflowPageToolbar, self).init_from_request()
        if self.page:
            self.title = self.page.title_set.filter(language=self.current_lang).first()
            self.workflow = Workflow.get_workflow(self.title)
            self.current_request = Action.get_current_request(self.title)
            self.current_action = Action.get_current_action(self.title)
            self.user = self.request.user
            self.next_stage = self.current_action.get_next_stage(self.user) if self.current_action else None
            self.editable = Action.is_editable(self.title)
            self.in_app = self.in_apphook() and not self.in_apphook_root()

    def has_publish_permission(self):
        if getattr(self, 'workflow', None):
            if self.current_request is None or not self.current_request.is_publishable():
                return False
        return super(WorkflowPageToolbar, self).has_publish_permission()

    def has_compare_permission(self):
        if not self.has_dirty_objects():
            return False

        return True

    def has_permission(self, action_type):
        if getattr(self, 'workflow', None) is None:
            return False
        if action_type == Action.CANCEL:
            return self.current_request is not None and not self.current_request.is_closed()
        if action_type == Action.REQUEST:
            if not self.has_dirty_objects():
                return False
            return self.current_request is None or self.current_request.is_closed()
        if action_type in (Action.APPROVE, Action.REJECT):
            return self.current_action and self.current_action.get_next_stage(self.user)
        if action_type == Action.DIFF:
            return self.has_dirty_objects()
        raise ValueError('Unknown action_type: {}'.format(action_type))

    def _button(self, action_type):
        with translation.override(self.current_lang):
            url = admin_reverse(
                self.WORKFLOW_URL_NAME.format(action_type),
                args=[self.page.pk, self.current_lang],
            )
        return ModalButton(name=self.BUTTON_NAMES[action_type], url=url)

    def add_button(self, menu, action_type):
        if self.has_permission(action_type):
            menu.buttons.append(self._button(action_type))

    def add_action_admin_button(self, menu):
        if self.current_request:
            opts = Action._meta
            button = SideframeButton(
                name=_('Show current request in admin'),
                url=admin_reverse(
                    '{app_label}_{model_name}_change'.format(
                        app_label=opts.app_label,
                        model_name=opts.model_name
                    ),
                    args=[self.current_request.pk])
            )
            menu.buttons.append(button)

    def post_template_populate(self):
        self.init_placeholders()
        self.add_draft_live()
        self.add_publish_menu()
        self.add_compare_button()

    def add_publish_button(self, classes=('cms-btn-action', 'cms-btn-publish',)):
        # only do dirty lookups if publish permission is granted else button isn't added anyway
        if self.toolbar.edit_mode and self.has_publish_permission():
            button = self.get_publish_button(classes=classes)
            self.toolbar.add_item(button)

    def add_compare_button(self):
        # only do dirty lookups if compare permission is granted else button isn't added
        if self.toolbar.edit_mode and self.has_compare_permission():
            button_list = ButtonList(side=self.toolbar.RIGHT)
            self.add_button(button_list, Action.DIFF)
            self.toolbar.add_item(button_list)

    def add_publish_menu(self, classes=('cms-btn-action', 'cms-btn-publish', 'cms-btn-publish-active',)):
        if self.in_app:
            return
        workflow_dropdown = Dropdown(side=self.toolbar.RIGHT)
        workflow_dropdown.add_primary_button(
            DropdownToggleButton(name=_('Publish'))
        )
        if self.has_publish_permission():
            workflow_dropdown.buttons.extend(self.get_publish_button(
                classes=('cms-btn-action', 'cms-btn-publish', 'cms-btn-publish-active')).buttons)
        for action_type in (Action.REQUEST, Action.APPROVE, Action.REJECT, Action.CANCEL):
            self.add_button(workflow_dropdown, action_type)
        self.add_action_admin_button(workflow_dropdown)
        if workflow_dropdown.buttons:
            self.toolbar.add_item(workflow_dropdown)


class EditorToolbar(CMSToolbar):
    def populate(self):
        action_dropdown = Dropdown(side=self.toolbar.RIGHT,)
        action_dropdown.add_primary_button(
            DropdownToggleButton(name=_('Pending your approval'))
        )
        actions = Action.requiring_action(self.request.user)
        if actions:
            opts = Action._meta
            view = '{app_label}_{model_name}_change'.format(
                app_label=opts.app_label,
                model_name=opts.model_name
            )
            for a in actions:
                button = SideframeButton(
                    name=str(a.title),
                    url=admin_reverse(view, args=[a.get_request().pk])
                )
                action_dropdown.buttons.append(button)
            self.toolbar.add_item(action_dropdown)


toolbar_pool.register(EditorToolbar)
toolbar_pool.register(WorkflowExtensionToolbar)
toolbar_pool.toolbars['cms.cms_toolbars.PlaceholderToolbar'] = WorkflowPlaceholderToolbar
toolbar_pool.toolbars['cms.cms_toolbars.PageToolbar'] = WorkflowPageToolbar
