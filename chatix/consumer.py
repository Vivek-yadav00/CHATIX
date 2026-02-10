from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
import json


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return

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
        
        # Use authenticated user from scope, ignore "sender" in payload for security
        sender_user = self.user
        sender_username = sender_user.username

        room = await self.get_room_safe(self.room_id)

        # 🚫 ROOM DELETED
        if room is None:
            await self.send(json.dumps({
                "type": "room_deleted"
            }))
            await self.close()
            return

        await self.update_last_seen(sender_user)  # Update last seen on message send
        msg_instance = await self.save_message(room, sender_user, message)

        # 🔥 UNHIDE ROOM & NOTIFY PARTICIPANTS
        participants = await self.get_participants(room)
        for p in participants:
            if p != sender_user:  # Don't notify sender, but ensure room is visible
                await self.unhide_room_for_user(room, p)
                
                await self.channel_layer.group_send(
                    f"user_{p.id}",
                    {
                        "type": "chat_notification",
                        "room_id": self.room_id,
                        "room_name": room.name,
                        "sender": sender_username,
                        "message": message,
                    }
                )
        
        # Ensure visible for sender too (if they deleted it previously)
        await self.unhide_room_for_user(room, sender_user)

        # Get Avatar URL
        avatar_url = None
        try:
            user_info = await database_sync_to_async(lambda: sender_user.userinfo)()
            if user_info.image:
                avatar_url = user_info.image.url
        except:
            pass

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": sender_username,
                "avatar_url": avatar_url,
                "message_id": msg_instance.id 
            }
        )

    async def chat_message(self, event):
        await self.send(json.dumps({
            "type": "chat",
            "message": event["message"],
            "sender": event["sender"],
            "avatar_url": event.get("avatar_url"),
            "message_id": event.get("message_id")
        }))

    async def room_deleted(self, event):
        await self.send(json.dumps({
            "type": "room_deleted"
        }))
        await self.close()

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
        "type": "message_deleted",
        "message_id": event["message_id"]
    }))


    # =====================
    # DATABASE HELPERS
    # =====================

    @database_sync_to_async
    def save_message(self, room, user, message):
        from .models import Message
        return Message.objects.create(
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
    def get_participants(self, room):
        return list(room.participants.all())

    @database_sync_to_async
    def get_user(self, username):
        from django.contrib.auth.models import User
        return User.objects.get(username=username)

    @database_sync_to_async
    def unhide_room_for_user(self, room, user):
        room.hidden_for.remove(user)

    @database_sync_to_async
    def update_last_seen(self, user):
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_notification(self, event):
        await self.send(json.dumps({
            "type": "notification",
            "room_id": event["room_id"],
            "room_name": event["room_name"],
            "sender": event["sender"],
            "message": event["message"]
        }))
