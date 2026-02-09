from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import ChatRoom, Message, UserInfo


# ---------- AUTH ----------

def Login(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )

        if user:
            if user.is_superuser:
                messages.error(request, "Admin must login via admin panel")
                return redirect("login")

            login(request, user)
            return redirect("index")

        messages.error(request, "Invalid credentials")

    return render(request, "chatix/login.html")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        image = request.FILES.get("image")

        # ❌ Empty field check
        if not all([username, password, name, email, phone]):
            messages.error(request, "All fields are required")
            return redirect("register")

        # ❌ Username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already registered")
            return redirect("register")

        # ❌ Email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        # ❌ Phone exists
        if UserInfo.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already registered")
            return redirect("register")

        # ❌ Phone length check (MODEL SAFE)
        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits")
            return redirect("register")

        # ❌ Password length check
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long")
            return redirect("register")

        # ✅ Create User
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        # ✅ Create UserInfo
        UserInfo.objects.create(
            user=user,
            name=name,
            email=email,
            phone=phone,
            image=image
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "chatix/register.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------- DASHBOARD ----------

@login_required
def index(request):
    chatrooms = ChatRoom.objects.filter(
        participants=request.user
    ).exclude(
        hidden_for=request.user
    )

    return render(request, "chatix/index.html", {
        "chatrooms": chatrooms
    })


# ---------- SEARCH ----------

@login_required
def search(request):
    query = request.GET.get("q", "")
    users = []

    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(userinfo__name__icontains=query) |
            Q(userinfo__email__icontains=query)
        ).exclude(id=request.user.id)

    return render(request, "chatix/search.html", {
        "users": users,
        "query": query
    })


# ---------- CHAT ROOM ----------

@login_required
def chatroom(request, id):
    room = get_object_or_404(ChatRoom, id=id)

    if request.user not in room.participants.all():
        return redirect("index")

    messages_qs = room.messages.all().exclude(deleted_for=request.user)
    
    # Get the other user
    other_user = None
    is_active = False
    for p in room.participants.all():
        if p != request.user:
            other_user = p
            # Check if active (within 5 minutes)
            if p.last_login:
                from django.utils import timezone
                from datetime import timedelta
                is_active = (timezone.now() - p.last_login) < timedelta(minutes=5)
            break

    return render(request, "chatix/chatroom.html", {
        "room": room,
        "messages": messages_qs,
        "other_user": other_user,
        "is_active": is_active
    })


# ---------- CREATE / OPEN CHAT ----------

@login_required
def add_user_to_chatroom(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    sender = request.user

    chatroom = ChatRoom.objects.filter(
        participants=sender
    ).filter(
        participants=receiver
    ).first()

    if not chatroom:
        chatroom = ChatRoom.objects.create(
            name=f"{sender.username} & {receiver.username}"
        )
        chatroom.participants.add(sender, receiver)

    chatroom.hidden_for.remove(sender)
    return redirect("chatroom", chatroom.id)


# ---------- DELETE CHAT (FOR ME ONLY) ----------

@login_required
def delete_chatroom(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    room.hidden_for.add(request.user)
    
    # Also hide all messages for this user
    for msg in room.messages.all():
        msg.deleted_for.add(request.user)

    return JsonResponse({"status": "ok"})


# ---------- DELETE MESSAGE (FIXED & WORKING) ----------

@login_required
def delete_message(request, msg_id):
    if request.method != "POST":
        return JsonResponse({"status": "invalid"}, status=400)

    msg = get_object_or_404(Message, id=msg_id)

    if msg.sender != request.user and not request.user.is_superuser:
        return JsonResponse({"status": "forbidden"}, status=403)

    room_id = msg.chatroom.id
    msg.delete()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_id}",
        {
            "type": "message_deleted",
            "message_id": msg_id,
        }
    )

    return JsonResponse({"status": "ok"})


# ---------- FAVORITES ----------

@login_required
def favorites(request):
    """View all favorite chats"""
    favorite_rooms = ChatRoom.objects.filter(
        favorited_by=request.user,
        participants=request.user
    ).exclude(hidden_for=request.user)
    
    return render(request, "chatix/favorites.html", {
        "chatrooms": favorite_rooms
    })


@login_required
def toggle_favorite(request, room_id):
    """Toggle favorite status of a chat"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if request.user not in room.participants.all():
        return JsonResponse({"status": "forbidden"}, status=403)
    
    if request.user in room.favorited_by.all():
        room.favorited_by.remove(request.user)
        is_favorite = False
    else:
        room.favorited_by.add(request.user)
        is_favorite = True
    
    return JsonResponse({"status": "ok", "is_favorite": is_favorite})