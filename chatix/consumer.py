from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
import json


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        room_exists = await self.room_exists(self.room_id)
        if not room_exists:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        message = data.get("message")
        sender = data.get("sender")

        room = await self.get_room_safe(self.room_id)

        # 🚫 ROOM DELETED
        if room is None:
            await self.send(json.dumps({
                "type": "room_deleted"
            }))
            await self.close()
            return

        user = await self.get_user(sender)
        await self.save_message(room, user, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": sender,
            }
        )

    async def chat_message(self, event):
        await self.send(json.dumps({
            "type": "chat",
            "message": event["message"],
            "sender": event["sender"]
        }))

    async def room_deleted(self, event):
        await self.send(json.dumps({
            "type": "room_deleted"
        }))
        await self.close()

    # =====================
    # DATABASE HELPERS
    # =====================

    @database_sync_to_async
    def save_message(self, room, user, message):
        from .models import Message
        Message.objects.create(
            chatroom=room,
            sender=user,
            content=message
        )

    @database_sync_to_async
    def get_room_safe(self, room_id):
        from .models import ChatRoom
        try:
            return ChatRoom.objects.get(id=room_id)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def room_exists(self, room_id):
        from .models import ChatRoom
        return ChatRoom.objects.filter(id=room_id).exists()

    @database_sync_to_async
    def get_user(self, username):
        from django.contrib.auth.models import User
        return User.objects.get(username=username)
