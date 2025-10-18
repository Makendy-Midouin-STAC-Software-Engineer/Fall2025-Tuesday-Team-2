from django.contrib import admin
from .models import Note, Room, Message, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_verified', 'token_created_at']
    list_filter = ['email_verified']
    search_fields = ['user__username', 'user__email']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'content', 'user__username']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'created_by__username']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'content_preview', 'timestamp']
    list_filter = ['timestamp', 'room']
    search_fields = ['content', 'user__username', 'room__name']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
