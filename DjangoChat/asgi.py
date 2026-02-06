"""
ASGI config for DjangoChat project.

It exposes the ASGI callable as a module-level variable named `application`.

This file supports both HTTP and WebSocket connections using Django Channels.
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import chatix.routing

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoChat.settings')

# Create ASGI application
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                chatix.routing.websocket_urlpatterns
            )
        ),
    }
)
