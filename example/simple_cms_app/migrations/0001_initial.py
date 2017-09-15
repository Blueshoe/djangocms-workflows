# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0017_auto_20170915_1201'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimpleModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=63, verbose_name='Name')),
                ('content', cms.models.fields.PlaceholderField(null=True, slotname='content', to='cms.Placeholder', editable=False)),
            ],
        ),
    ]
