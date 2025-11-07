from django.db import models
from django.conf import settings
from jobs.models import Application


class ChatRequest(models.Model):
    """Request to start a conversation about a job application"""
    PENDING = 'P'
    APPROVED = 'A'
    REJECTED = 'R'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='chat_requests')
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_chat_requests')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_chat_requests')
    message = models.TextField(help_text='Why do you want to start this conversation?')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['application', 'requester', 'recipient']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Chat request from {self.requester.username} to {self.recipient.username}"


class Conversation(models.Model):
    """A conversation between two users about a specific job application"""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='conversations')
    participant_1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_p1')
    participant_2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_p2')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text='Admin can deactivate if conversation violates business conduct')
    
    class Meta:
        unique_together = ['application', 'participant_1', 'participant_2']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Conversation: {self.participant_1.username} & {self.participant_2.username} about {self.application.job.title}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if user == self.participant_1:
            return self.participant_2
        return self.participant_1


class Message(models.Model):
    """Individual message in a conversation - strictly business only, admin visible"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(help_text='Keep messages strictly business-related')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    flagged_by_admin = models.BooleanField(default=False, help_text='Admin can flag inappropriate messages')
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"
