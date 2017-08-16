# -*- coding: utf-8 -*-
from cms.cms_toolbars import PlaceholderToolbar, PageToolbar
from cms.toolbar.items import ModalButton, Dropdown, DropdownToggleButton
from cms.toolbar_pool import toolbar_pool
from cms.extensions.toolbar import ExtensionToolbar
from cms.utils.urlutils import admin_reverse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _


from workflows.models import Action, Workflow
from .models import WorkflowExtension
from cms.utils import get_language_list  # needed to get the page's languages


def get_page_toolbar():
    try:
        return toolbar_pool.toolbars.pop('cms.cms_toolbars.PageToolbar')
    except KeyError:
        return PageToolbar


def get_placeholder_toolbar():
    try:
        return toolbar_pool.toolbars.pop('cms.cms_toolbars.PlaceholderToolbar')
    except KeyError:
        return PlaceholderToolbar


# @toolbar_pool.register
class RatingExtensionToolbar(ExtensionToolbar):
    # As described in the docs

    # defines the model for the current toolbar
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

            # we now also need to get the titleset (i.e. different language titles) for this page
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
            self.toolbar.content_renderer._placeholders_are_editable = self.editable

    def add_structure_mode(self):
        if self.editable:
            return super(WorkflowPlaceholderToolbar, self).add_structure_mode()


class WorkflowPageToolbar(PageToolbar):
    WORKFLOW_URL_NAME = 'workflow_{}'
    BUTTON_NAMES = {
        Action.REQUEST: _('Request'),
        Action.APPROVE: _('Approve'),
        Action.REJECT: _('Reject'),
        Action.CANCEL: _('Cancel'),
    }

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

    def has_publish_permission(self):
        if getattr(self, 'workflow', None):
            if self.current_request is None or not self.current_request.is_publishable():
                return False
        return super(WorkflowPageToolbar, self).has_publish_permission()

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

    def post_template_populate(self):
        self.init_placeholders()
        self.add_draft_live()
        self.add_publish_menu()

    def add_publish_button(self, classes=('cms-btn-action', 'cms-btn-publish',)):
        # only do dirty lookups if publish permission is granted else button isn't added anyway
        if self.toolbar.edit_mode and self.has_publish_permission():
            button = self.get_publish_button(classes=classes)
            self.toolbar.add_item(button)

    def add_publish_menu(self, classes=('cms-btn-action', 'cms-btn-publish', 'cms-btn-publish-active',)):
        workflow_dropdown = Dropdown(side=self.toolbar.RIGHT)
        workflow_dropdown.add_primary_button(
            DropdownToggleButton(name=_('Publish'))
        )
        if self.has_publish_permission():
            workflow_dropdown.buttons.extend(self.get_publish_button(
                classes=('cms-btn-action', 'cms-btn-publish', 'cms-btn-publish-active')).buttons)
        for action_type in (Action.REQUEST, Action.APPROVE, Action.REJECT, Action.CANCEL):
            self.add_button(workflow_dropdown, action_type)
        if workflow_dropdown.buttons:
            self.toolbar.add_item(workflow_dropdown)

    # def get_publish_button(self, classes=None):
    #     button = super(ExtendedPageToolbar, self).get_publish_button(['cms-btn-publish'])
    #     publish_dropdown = Dropdown(side=self.toolbar.RIGHT)
    #     publish_dropdown.add_primary_button(
    #         DropdownToggleButton(name=_('Moderation'))
    #     )
    #     publish_dropdown.buttons.extend(button.buttons)
    #     publish_dropdown.buttons.append(self.get_cancel_moderation_button())
    #     return publish_dropdown


# print(toolbar_pool.toolbars)

toolbar_pool.register(RatingExtensionToolbar)
toolbar_pool.toolbars['cms.cms_toolbars.PlaceholderToolbar'] = WorkflowPlaceholderToolbar
toolbar_pool.toolbars['cms.cms_toolbars.PageToolbar'] = WorkflowPageToolbar
