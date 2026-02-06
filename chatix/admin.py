from django.contrib import admin
from .models import UserInfo,ChatRoom, Message

    
# Register your models here.

class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email', 'phone', 'image')
    search_fields = ('name', 'email')
    list_filter = ('user__is_active',)
    ordering = ('name',)

admin.site.register(UserInfo, UserInfoAdmin)
admin.site.register(ChatRoom)
admin.site.register(Message)