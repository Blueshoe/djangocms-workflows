# -*- coding: utf-8 -*-

from .base import *


DATABASES = {
    'default': {
        'CONN_MAX_AGE': 0,
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pipelines',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'USER': 'blueshoe',
        'PASSWORD': 'blueshoe',
    }
}

