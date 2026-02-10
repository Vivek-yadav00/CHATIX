"""
ASGI config for DjangoChat project.

It exposes the ASGI callable as a module-level variable named `application`.

This file supports both HTTP and WebSocket connections using Django Channels.
"""

import os
from django.core.asgi import get_asgi_application

# Set default Django settings module BEFORE any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoChat.settings')

# Initialize Django ASGI application early to ensure apps are loaded
django_asgi_app = get_asgi_application()

# NOW import Channels components (after Django is initialized)
from channels.security.websocket import AllowedHostsOriginValidator

# Create ASGI application
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    chatix.routing.websocket_urlpatterns
                )
            )
        ),
    }
)
