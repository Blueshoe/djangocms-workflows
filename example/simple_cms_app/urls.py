# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic import TemplateView

from .views import SimpleView, SimpleListView

urlpatterns = [
    # url(r'^$', TemplateView.as_view(template_name='simple_cms_app/index.html'), name='index'),
    url(r'^$', SimpleListView.as_view(), name='list'),
    url(r'^detail/(?P<pk>\d+)/$', SimpleView.as_view(), name='detail'),
]
