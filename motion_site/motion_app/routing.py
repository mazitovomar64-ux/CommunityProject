from django.urls import path
from .consumers import ChatConsumer

websocket_url_patterns = [
    path('ws/chat/<str:room_name>/', ChatConsumer.as_asgi())
]