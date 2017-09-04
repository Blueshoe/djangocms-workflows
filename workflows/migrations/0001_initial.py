# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        # ('cms', '0018_auto_20170825_1058'),
        ('cms', '0016_auto_20160608_1535'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('action_type', models.CharField(choices=[('request', 'request'), ('approve', 'approve'), ('reject', 'reject'), ('cancel', 'cancel'), ('publish', 'publish'), ('diff', 'diff')], default='request', max_length=10, verbose_name='Action type')),
                ('created', models.DateTimeField(verbose_name='Created', auto_now_add=True)),
                ('message', models.TextField(verbose_name='Message')),
                ('group', models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, verbose_name='Group', null=True, to='auth.Group')),
            ],
            options={
                'verbose_name': 'Workflow action',
                'verbose_name_plural': 'Workflow actions',
                'ordering': ('depth', 'created'),
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(verbose_name='Name', unique=True, help_text='Please provide a descriptive name!', max_length=63)),
                ('default', models.BooleanField(default=False, help_text='Should this be the default workflow for all pages and languages?', verbose_name='Default workflow')),
            ],
            options={
                'verbose_name': 'Workflow',
                'verbose_name_plural': 'Workflows',
            },
        ),
        migrations.CreateModel(
            name='WorkflowExtension',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('descendants', models.BooleanField(default=True, help_text='Should this workflow apply to descendant pages?', verbose_name='Descendants')),
                ('extended_object', models.OneToOneField(editable=False, to='cms.Title')),
                ('public_extension', models.OneToOneField(related_name='draft_extension', null=True, editable=False, to='workflows.WorkflowExtension')),
                ('workflow', models.ForeignKey(help_text='The workflow set here is language specific.', verbose_name='Workflow', to='workflows.Workflow')),
            ],
            options={
                'verbose_name': 'Workflow extension',
                'verbose_name_plural': 'Workflow extensions',
            },
        ),
        migrations.CreateModel(
            name='WorkflowStage',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(verbose_name='Order', default=0)),
                ('optional', models.BooleanField(default=False, help_text='Is this workflow stage optional?', verbose_name='Optional')),
                ('group', models.ForeignKey(help_text='Only members of this group can approve this workflow stage.', on_delete=django.db.models.deletion.PROTECT, verbose_name='Group', to='auth.Group')),
                ('workflow', models.ForeignKey(related_name='stages', verbose_name='Workflow', to='workflows.Workflow')),
            ],
            options={
                'verbose_name': 'Workflow stage',
                'verbose_name_plural': 'Workflow stages',
                'ordering': ('order',),
            },
        ),
        migrations.AddField(
            model_name='action',
            name='stage',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_NULL, verbose_name='Stage', null=True, to='workflows.WorkflowStage'),
        ),
        migrations.AddField(
            model_name='action',
            name='title',
            field=models.ForeignKey(verbose_name='Title', to='cms.Title'),
        ),
        migrations.AddField(
            model_name='action',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='action',
            name='workflow',
            field=models.ForeignKey(verbose_name='Workflow', to='workflows.Workflow'),
        ),
        migrations.AlterUniqueTogether(
            name='workflowstage',
            unique_together=set([('workflow', 'group')]),
        ),
    ]
