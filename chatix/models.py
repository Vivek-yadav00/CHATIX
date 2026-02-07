from django.db import models
from django.contrib.auth.models import User


# =========================
# USER PROFILE
# =========================
class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10, unique=True)
    image = models.ImageField(upload_to="profile_images/", blank=True, null=True)

    def __str__(self):
        return self.name


# =========================
# CHAT ROOM (WhatsApp style)
# =========================
class ChatRoom(models.Model):
    name = models.CharField(max_length=100)

    participants = models.ManyToManyField(
        User,
        related_name="chatrooms"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 "Delete for me" (room hidden only for that user)
    hidden_for = models.ManyToManyField(
        User,
        related_name="hidden_chatrooms",
        blank=True
    )

    def is_visible_for(self, user):
        """Check if room is visible for a user"""
        return user not in self.hidden_for.all()

    def hide_for_user(self, user):
        """Hide room for a user (WhatsApp delete chat)"""
        self.hidden_for.add(user)

    def __str__(self):
        return self.name


# =========================
# MESSAGE (WhatsApp style)
# =========================
class Message(models.Model):
    chatroom = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 "Delete for me" (message hidden only for selected users)
    deleted_for = models.ManyToManyField(
        User,
        related_name="deleted_messages",
        blank=True
    )

    class Meta:
        ordering = ["created_at"]

    # ---------- HELPERS ----------

    def is_visible_for(self, user):
        """Check if message is visible for a user"""
        return user not in self.deleted_for.all()

    def delete_for_user(self, user):
        """Delete message only for one user"""
        self.deleted_for.add(user)

    def delete_for_everyone(self):
        """Delete message globally"""
        self.delete()

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"
