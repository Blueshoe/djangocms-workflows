from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.views.generic import TemplateView

from example.simple_cms_app.models import SimpleModel


class SimpleView(TemplateView):
    template_name = 'simple_cms_app/detail.html'

    def get_context_data(self, **kwargs):
        kwargs['simple_model'] = get_object_or_404(SimpleModel, pk=self.kwargs.get('pk'))
        return super(SimpleView, self).get_context_data(**kwargs)


class SimpleListView(TemplateView):
    template_name = 'simple_cms_app/list.html'

    def get_context_data(self, **kwargs):
        kwargs['simple_models'] = SimpleModel.objects.all()
        return super(SimpleListView, self).get_context_data(**kwargs)

