# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cms', '0017_auto_20170823_1107'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('action_type', models.CharField(default='request', max_length=10, choices=[('request', 'request'), ('approve', 'approve'), ('reject', 'reject'), ('cancel', 'cancel'), ('publish', 'publish')], verbose_name='Action type')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('message', models.TextField(verbose_name='Message')),
                ('group', models.ForeignKey(to='auth.Group', on_delete=django.db.models.deletion.PROTECT, default=None, verbose_name='Group', null=True)),
            ],
            options={
                'verbose_name_plural': 'Workflow actions',
                'ordering': ('depth', 'created'),
                'verbose_name': 'Workflow action',
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=63, help_text='Please provide a descriptive name!', verbose_name='Name')),
                ('default', models.BooleanField(default=False, help_text='Should this be the default workflow for all pages and languages?', verbose_name='Default workflow')),
            ],
            options={
                'verbose_name_plural': 'Workflows',
                'verbose_name': 'Workflow',
            },
        ),
        migrations.CreateModel(
            name='WorkflowExtension',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('descendants', models.BooleanField(default=True, help_text='Should this workflow apply to descendant pages?', verbose_name='Descendants')),
                ('extended_object', models.OneToOneField(editable=False, to='cms.Title')),
                ('public_extension', models.OneToOneField(editable=False, related_name='draft_extension', to='workflows.WorkflowExtension', null=True)),
                ('workflow', models.ForeignKey(to='workflows.Workflow', help_text='The workflow set here is language specific.', verbose_name='Workflow')),
            ],
            options={
                'verbose_name_plural': 'Workflow extensions',
                'verbose_name': 'Workflow extension',
            },
        ),
        migrations.CreateModel(
            name='WorkflowStage',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Order')),
                ('optional', models.BooleanField(default=False, help_text='Is this workflow stage optional?', verbose_name='Optional')),
                ('group', models.ForeignKey(to='auth.Group', on_delete=django.db.models.deletion.PROTECT, help_text='Only members of this group can approve this workflow stage.', verbose_name='Group')),
                ('workflow', models.ForeignKey(to='workflows.Workflow', related_name='stages', verbose_name='Workflow')),
            ],
            options={
                'verbose_name_plural': 'Workflow stages',
                'ordering': ('order',),
                'verbose_name': 'Workflow stage',
            },
        ),
        migrations.AddField(
            model_name='action',
            name='stage',
            field=models.ForeignKey(to='workflows.WorkflowStage', on_delete=django.db.models.deletion.SET_NULL, default=None, verbose_name='Stage', null=True),
        ),
        migrations.AddField(
            model_name='action',
            name='title',
            field=models.ForeignKey(to='cms.Title', verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='action',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='User', null=True),
        ),
        migrations.AddField(
            model_name='action',
            name='workflow',
            field=models.ForeignKey(to='workflows.Workflow', verbose_name='Workflow'),
        ),
        migrations.AlterUniqueTogether(
            name='workflowstage',
            unique_together=set([('workflow', 'group')]),
        ),
    ]
