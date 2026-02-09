from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from .views import (
    Login, register, logout_view, settings_view,
    index, search, chatroom,
    add_user_to_chatroom,
    delete_chatroom, delete_message,
    favorites, toggle_favorite
)

urlpatterns = [
    path("", Login, name="login"),
    path("login/", Login, name="login"),
    path("register/", register, name="register"),
    path("settings/", settings_view, name="settings"),
    path("logout/", logout_view, name="logout"),

    # Password Change
    path("password-change/", auth_views.PasswordChangeView.as_view(template_name='chatix/change_password.html', success_url='/password-change/done/'), name='password_change'),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(template_name='chatix/password_change_done.html'), name='password_change_done'),

    path("index/", index, name="index"),
    path("search/", search, name="search"),
    path("favorites/", favorites, name="favorites"),

    path("chatroom/<int:id>/", chatroom, name="chatroom"),
    path("add-user/<int:user_id>/", add_user_to_chatroom, name="add_user_to_chatroom"),

    path("room/delete/<int:room_id>/", delete_chatroom, name="delete_chatroom"),
    path("room/toggle-favorite/<int:room_id>/", toggle_favorite, name="toggle_favorite"),
    path("delete-message/<int:msg_id>/", delete_message, name="delete_message"),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
