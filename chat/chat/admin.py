from django.contrib import admin
from .models import Chat, Message, UserProfile

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_group_chat')
    filter_horizontal = ('participants',)
    search_fields = ('name', 'participants__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chat', 'content', 'timestamp', 'is_edited')
    list_filter = ('chat', 'sender', 'timestamp')
    search_fields = ('content', 'sender__username')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')
    search_fields = ('user__username',)
