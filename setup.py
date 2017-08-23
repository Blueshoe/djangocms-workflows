#!/usr/bin/env python
import os
import uuid
import workflows

from pip.req import parse_requirements

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requirements = [str(ir.req) for ir in parse_requirements('requirements.txt', session=uuid.uuid1())]

setup(
    name=workflows.__name__,
    version=workflows.__version__,
    description='Workflow system for Django-CMS users which aims for ease of use.',
    long_description=read('README.md'),
    license=read('LICENSE'),
    author='Blueshoe',
    author_email='TODO@TODO.com',
    url='https://github.com/Blueshoe/djangocms-workflows',
    packages=['workflows'],
    include_package_data=True,
    install_requires=requirements,
    keywords=['django', 'Django CMS', 'workflow', 'bootstrap', 'website', 'CMS', 'Blueshoe'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
)