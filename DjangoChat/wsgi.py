"""
WSGI config for DjangoChat project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""
# WEB SERVER GATEWAY INTERFACE (WSGI) CONFIGURATION
# This file is used to deploy the Django application using WSGI-compatible web servers.
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoChat.settings')

application = get_wsgi_application()
