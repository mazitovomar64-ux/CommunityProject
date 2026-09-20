"""
ASGI config for motion_site project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motion_site.settings')

django_asgi_app = get_asgi_application()

from motion_app.routing import websocket_url_patterns
from motion_app.ws_auth import JWTAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(
            URLRouter(
                websocket_url_patterns
            )
        )
    }
)
