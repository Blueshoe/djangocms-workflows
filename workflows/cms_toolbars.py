# -*- coding: utf-8 -*-

from cms.toolbar_pool import toolbar_pool
from cms.extensions.toolbar import ExtensionToolbar
from django.utils.translation import ugettext_lazy as _
from .models import WorkflowExtension
from cms.utils import get_language_list  # needed to get the page's languages


@toolbar_pool.register
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
