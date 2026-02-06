from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q

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
        user = User.objects.create_user(
            username=request.POST["username"],
            password=request.POST["password"],
            email=request.POST["email"]
        )

        UserInfo.objects.create(
            user=user,
            name=request.POST["name"],
            email=request.POST["email"],
            phone=request.POST["phone"],
            image=request.FILES.get("image")
        )

        login(request, user)
        return redirect("index")

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
        hidden_for=request.user   # ✅ FIXED FIELD
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

    messages_qs = room.messages.exclude(
        deleted_for=request.user   # ✅ CORRECT
    )

    return render(request, "chatix/chatroom.html", {
        "room": room,
        "messages": messages_qs
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

    # if chat was hidden earlier → restore
    chatroom.hidden_for.remove(sender)

    return redirect("chatroom", chatroom.id)


# ---------- DELETE CHAT (FOR ME ONLY) ----------

@login_required
def delete_chatroom(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    room.hidden_for.add(request.user)
    return JsonResponse({"status": "ok"})


# ---------- DELETE MESSAGE (FOR ME ONLY) ----------

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if request.user != message.sender:
        return HttpResponseForbidden()

    message.deleted_for.add(request.user)
    return JsonResponse({"status": "ok"})
