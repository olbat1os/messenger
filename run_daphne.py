import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger_project.settings')
django.setup()

from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})

if __name__ == "__main__":
    from daphne.server import Server
    from daphne.endpoints import build_endpoint_description_strings

    server = Server(
        application=application,
        endpoints=build_endpoint_description_strings(host="0.0.0.0", port=8000),
        signal_handlers=True,
    )
    server.run() 