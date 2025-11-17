from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Note, Room, Message, UserProfile


# Customize User Admin to show more info and give more control
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = True
    verbose_name_plural = "Profile"
    fk_name = "user"
    fields = ["email_verified", "verification_token", "token_created_at"]
    readonly_fields = ["verification_token", "token_created_at"]


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
        "get_email_verified",
    ]
    list_filter = ["is_staff", "is_superuser", "is_active", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name"]
    actions = ["activate_users", "deactivate_users", "make_staff"]

    def get_email_verified(self, obj):
        try:
            return "✓" if obj.profile.email_verified else "✗"
        except UserProfile.DoesNotExist:
            return "?"

    get_email_verified.short_description = "Email Verified"

    # Bulk actions for user management
    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} users activated.")

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} users deactivated.")

    @admin.action(description="Make selected users staff")
    def make_staff(self, request, queryset):
        queryset.update(is_staff=True)
        self.message_user(request, f"{queryset.count()} users made staff.")


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "get_user_email", "email_verified", "token_created_at"]
    list_filter = ["email_verified", "token_created_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["verification_token", "token_created_at", "email_verified"]

    def get_user_email(self, obj):
        return obj.user.email

    get_user_email.short_description = "Email"

    # Note: Email verification should only happen via the verification link
    # to maintain security and proper email validation


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "created_at", "updated_at", "content_length"]
    list_filter = ["created_at", "updated_at", "user"]
    search_fields = ["title", "content", "user__username"]
    date_hierarchy = "created_at"
    actions = ["delete_selected_notes"]
    readonly_fields = ["created_at", "updated_at"]

    # Show all fields when editing
    fieldsets = (
        ("Note Information", {"fields": ("user", "title", "content")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def content_length(self, obj):
        return f"{len(obj.content)} chars"

    content_length.short_description = "Length"

    @admin.action(description="Delete selected notes")
    def delete_selected_notes(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} notes deleted.")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "created_by",
        "is_private",
        "created_at",
        "message_count",
        "timer_is_running",
        "timer_mode",
    ]
    list_filter = ["created_at", "created_by", "timer_is_running", "timer_mode"]
    search_fields = ["name", "description", "created_by__username"]
    date_hierarchy = "created_at"
    actions = ["delete_selected_rooms", "reset_all_timers"]
    readonly_fields = ["created_at", "message_count"]

    fieldsets = (
        ("Room Information", {"fields": ("name", "description", "created_by")}),
        (
            "Privacy Settings",
            {"fields": ("is_private", "password")},
        ),
        (
            "Pomodoro Timer",
            {
                "fields": (
                    "timer_is_running",
                    "timer_mode",
                    "timer_duration",
                    "timer_started_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Statistics",
            {"fields": ("created_at", "message_count"), "classes": ("collapse",)},
        ),
    )

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = "Messages"

    @admin.action(description="Delete selected rooms and all messages")
    def delete_selected_rooms(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} rooms deleted.")

    @admin.action(description="Reset timers for selected rooms")
    def reset_all_timers(self, request, queryset):
        queryset.update(
            timer_is_running=False,
            timer_started_at=None,
            timer_mode="work",
            timer_duration=1500,
        )
        self.message_user(request, f"{queryset.count()} timers reset.")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["user", "room", "content_preview", "timestamp", "id"]
    list_filter = ["timestamp", "room", "user"]
    search_fields = ["content", "user__username", "room__name"]
    date_hierarchy = "timestamp"
    actions = ["delete_selected_messages", "move_to_different_room"]
    readonly_fields = ["timestamp"]

    fieldsets = (
        ("Message Information", {"fields": ("room", "user", "content")}),
        ("Metadata", {"fields": ("timestamp",), "classes": ("collapse",)}),
    )

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content"

    @admin.action(description="Delete selected messages")
    def delete_selected_messages(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} messages deleted.")


# Customize admin site header and title
admin.site.site_header = "StudyBuddy Administration"
admin.site.site_title = "StudyBuddy Admin"
admin.site.index_title = "Welcome to StudyBuddy Admin Panel"
