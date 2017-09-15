from cms.models.fields import PlaceholderField
from django.db import models
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class SimpleModel(models.Model):
    name = models.CharField(_('Name'), max_length=63)
    content = PlaceholderField('content')
