from django.db import models
from django.contrib.auth.models import User


# =========================
# USER PROFILE
# =========================
class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
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

    # 🔥 Hide chat ONLY for selected users (Delete for me)
    hidden_for = models.ManyToManyField(
        User,
        related_name="hidden_chatrooms",
        blank=True
    )

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
        on_delete=models.CASCADE
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 Delete message ONLY for selected users
    deleted_for = models.ManyToManyField(
        User,
        related_name="deleted_messages",
        blank=True
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"
