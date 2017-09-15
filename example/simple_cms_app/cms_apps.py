# -*- coding: utf-8 -*-

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _


class SimpleCMSApphook(CMSApp):
    name = _("Simple CMS app Apphook")
    app_name = 'simple'

    def get_urls(self, page=None, language=None, **kwargs):
        return ["simple_cms_app.urls"]       # replace this with the path to your application's URLs module


apphook_pool.register(SimpleCMSApphook)
