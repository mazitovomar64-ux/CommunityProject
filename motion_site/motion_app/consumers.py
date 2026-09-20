import json

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer

from .models import Chat, Message


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

        if not self.chat.person.filter(pk=self.user.pk).exists():
            self.close(code=4003)
            return

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            text = data["message"].strip()
        except (json.JSONDecodeError, KeyError, AttributeError):
            self.send(text_data=json.dumps({"error": "invalid_payload"}))
            return

        if not text:
            return

        message = Message.objects.create(
            text=text,
            sender=self.user,
            chat=self.chat,
        )

        payload = {
            "type": "chat.message",
            "id": message.pk,
            "message": message.text,
            "sender_id": self.user.pk,
            "sender_name": self.user.get_full_name() or self.user.email,
            "send_time": message.send_time.isoformat(),
        }

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, payload
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))
