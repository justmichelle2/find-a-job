from django.contrib import admin
from .models import ChatRequest, Conversation, Message


@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    list_display = ['requester', 'recipient', 'application', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['requester__username', 'recipient__username', 'application__job__title']
    readonly_fields = ['created_at', 'responded_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['participant_1', 'participant_2', 'application', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['participant_1__username', 'participant_2__username', 'application__job__title']
    readonly_fields = ['created_at']
    actions = ['deactivate_conversations', 'activate_conversations']
    
    def deactivate_conversations(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} conversation(s) deactivated.")
    deactivate_conversations.short_description = "Deactivate selected conversations"
    
    def activate_conversations(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} conversation(s) activated.")
    activate_conversations.short_description = "Activate selected conversations"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'content_preview', 'timestamp', 'flagged_by_admin']
    list_filter = ['flagged_by_admin', 'timestamp']
    search_fields = ['sender__username', 'content', 'conversation__application__job__title']
    readonly_fields = ['timestamp']
    actions = ['flag_messages', 'unflag_messages']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Message Preview'
    
    def flag_messages(self, request, queryset):
        queryset.update(flagged_by_admin=True)
        self.message_user(request, f"{queryset.count()} message(s) flagged.")
    flag_messages.short_description = "Flag selected messages"
    
    def unflag_messages(self, request, queryset):
        queryset.update(flagged_by_admin=False)
        self.message_user(request, f"{queryset.count()} message(s) unflagged.")
    unflag_messages.short_description = "Unflag selected messages"
