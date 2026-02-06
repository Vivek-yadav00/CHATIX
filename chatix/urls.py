from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from .views import (
    Login, register, logout_view,
    index, search, chatroom,
    add_user_to_chatroom,
    delete_chatroom, delete_message
)

urlpatterns = [
    path("", Login, name="login"),
    path("login/", Login, name="login"),
    path("register/", register, name="register"),
    path("logout/", logout_view, name="logout"),

    path("index/", index, name="index"),
    path("search/", search, name="search"),

    path("chatroom/<int:id>/", chatroom, name="chatroom"),
    path("add-user/<int:user_id>/", add_user_to_chatroom, name="add_user_to_chatroom"),

    path("room/delete/<int:room_id>/", delete_chatroom, name="delete_chatroom"),
    path("message/delete/<int:message_id>/", delete_message, name="delete_message"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
