import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .chat import build_message_payload, can_access_chat
from .models import Chat, Message

MAX_MESSAGE_LENGTH = 2000


class ChatConsumer(WebsocketConsumer):


    def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            self.close(code=4001)
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        try:
            self.chat = Chat.objects.get(pk=self.room_name)
        except (Chat.DoesNotExist, ValueError):
            self.close(code=4004)
            return

        if not can_access_chat(self.user, self.chat):
            self.close(code=4003)
            return

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        if hasattr(self, "room_group_name") and hasattr(self, "chat"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            text = data["message"].strip()
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
            self.send(text_data=json.dumps({"error": "invalid_payload"}))
            return

        if not text:
            return

        if len(text) > MAX_MESSAGE_LENGTH:
            self.send(text_data=json.dumps({"error": "message_too_long"}))
            return

        message = Message.objects.create(
            text=text,
            sender=self.user,
            chat=self.chat,
        )

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, build_message_payload(message)
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))