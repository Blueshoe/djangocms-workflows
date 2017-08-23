# -*- coding: utf-8 -*-

from .base import *


DATABASES = {
    'default': {
        'CONN_MAX_AGE': 0,
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'workflows',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'USER': 'workflows',
        'PASSWORD': 'workflows',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
