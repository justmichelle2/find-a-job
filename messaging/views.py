from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import ChatRequest, Conversation, Message
from jobs.models import Application
from notifications.utils import create_notification
from notifications.models import Notification


@login_required
def request_chat(request, application_id):
    """Request to start a conversation about an application"""
    application = get_object_or_404(Application, pk=application_id)
    
    # Determine who the recipient should be
    if request.user == application.applicant:
        recipient = application.job.company
    elif request.user == application.job.company:
        recipient = application.applicant
    else:
        messages.error(request, "You are not authorized to request chat for this application.")
        return redirect('jobs:job_detail', pk=application.job.pk)
    
    # Check if request already exists
    existing_request = ChatRequest.objects.filter(
        application=application,
        requester=request.user,
        recipient=recipient
    ).first()
    
    if existing_request:
        if existing_request.status == ChatRequest.PENDING:
            messages.info(request, "You already have a pending chat request for this application.")
        elif existing_request.status == ChatRequest.APPROVED:
            messages.info(request, "Chat already approved. You can message now.")
            return redirect('messaging:conversation_detail', application_id=application.pk)
        elif existing_request.status == ChatRequest.REJECTED:
            messages.warning(request, "Your previous chat request was rejected.")
        return redirect('jobs:job_detail', pk=application.job.pk)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        if not message_text:
            messages.error(request, "Please provide a reason for the chat request.")
            return render(request, 'messaging/request_chat.html', {
                'application': application,
                'recipient': recipient
            })
        
        chat_request = ChatRequest.objects.create(
            application=application,
            requester=request.user,
            recipient=recipient,
            message=message_text
        )
        
        # Create notification for recipient
        create_notification(
            recipient=recipient,
            notification_type=Notification.EMAIL_VERIFIED,  # Using existing type, you can add custom one
            title=f"New chat request from {request.user.username}",
            message=f"{request.user.username} wants to discuss the application for {application.job.title}",
            related_application=application
        )
        
        messages.success(request, f"Chat request sent to {recipient.username}. You'll be notified when they respond.")
        return redirect('jobs:job_detail', pk=application.job.pk)
    
    return render(request, 'messaging/request_chat.html', {
        'application': application,
        'recipient': recipient
    })


@login_required
def chat_requests(request):
    """View all incoming and outgoing chat requests"""
    incoming = ChatRequest.objects.filter(recipient=request.user).select_related('requester', 'application__job')
    outgoing = ChatRequest.objects.filter(requester=request.user).select_related('recipient', 'application__job')
    
    return render(request, 'messaging/chat_requests.html', {
        'incoming': incoming,
        'outgoing': outgoing
    })


@login_required
def respond_to_chat_request(request, request_id, action):
    """Approve or reject a chat request"""
    chat_request = get_object_or_404(ChatRequest, pk=request_id, recipient=request.user)
    
    if chat_request.status != ChatRequest.PENDING:
        messages.warning(request, "This request has already been responded to.")
        return redirect('messaging:chat_requests')
    
    if action == 'approve':
        chat_request.status = ChatRequest.APPROVED
        chat_request.responded_at = timezone.now()
        chat_request.save()
        
        # Create conversation
        conversation, created = Conversation.objects.get_or_create(
            application=chat_request.application,
            participant_1=chat_request.requester,
            participant_2=chat_request.recipient
        )
        
        # Notify requester
        create_notification(
            recipient=chat_request.requester,
            notification_type=Notification.EMAIL_VERIFIED,
            title="Chat request approved",
            message=f"{request.user.username} approved your chat request. You can now message about {chat_request.application.job.title}",
            related_application=chat_request.application
        )
        
        messages.success(request, "Chat request approved. You can now start messaging.")
        return redirect('messaging:conversation_detail', application_id=chat_request.application.pk)
        
    elif action == 'reject':
        chat_request.status = ChatRequest.REJECTED
        chat_request.responded_at = timezone.now()
        chat_request.save()
        
        # Notify requester
        create_notification(
            recipient=chat_request.requester,
            notification_type=Notification.EMAIL_VERIFIED,
            title="Chat request declined",
            message=f"{request.user.username} declined your chat request for {chat_request.application.job.title}",
            related_application=chat_request.application
        )
        
        messages.info(request, "Chat request rejected.")
        return redirect('messaging:chat_requests')
    
    messages.error(request, "Invalid action.")
    return redirect('messaging:chat_requests')


@login_required
def conversations(request):
    """List all conversations for the current user"""
    user_conversations = Conversation.objects.filter(
        Q(participant_1=request.user) | Q(participant_2=request.user),
        is_active=True
    ).select_related('application__job', 'participant_1', 'participant_2').prefetch_related('messages')
    
    return render(request, 'messaging/conversations.html', {
        'conversations': user_conversations
    })


@login_required
def conversation_detail(request, application_id):
    """View and send messages in a conversation"""
    application = get_object_or_404(Application, pk=application_id)
    
    # Find the conversation
    conversation = Conversation.objects.filter(
        application=application,
        is_active=True
    ).filter(
        Q(participant_1=request.user, participant_2=application.job.company if request.user == application.applicant else application.applicant) |
        Q(participant_1=application.job.company if request.user == application.applicant else application.applicant, participant_2=request.user)
    ).first()
    
    if not conversation:
        messages.error(request, "No active conversation found. You may need to request chat first.")
        return redirect('jobs:job_detail', pk=application.job.pk)
    
    # Check user is a participant
    if request.user not in [conversation.participant_1, conversation.participant_2]:
        messages.error(request, "You are not part of this conversation.")
        return redirect('jobs:job_list')
    
    # Handle sending a message
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            # Notify other participant
            other_user = conversation.get_other_participant(request.user)
            create_notification(
                recipient=other_user,
                notification_type=Notification.EMAIL_VERIFIED,
                title=f"New message from {request.user.username}",
                message=f"{request.user.username}: {content[:50]}{'...' if len(content) > 50 else ''}",
                related_application=application
            )
            
            return redirect('messaging:conversation_detail', application_id=application_id)
        else:
            messages.error(request, "Message cannot be empty.")
    
    # Mark messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    # Get all messages
    message_list = conversation.messages.all().select_related('sender')
    
    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'messages': message_list,
        'application': application,
        'other_user': conversation.get_other_participant(request.user)
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_monitor_conversations(request):
    """Admin view to monitor all conversations for business compliance"""
    all_conversations = Conversation.objects.all().select_related(
        'application__job',
        'participant_1',
        'participant_2'
    ).prefetch_related('messages')
    
    # Filter options
    show_inactive = request.GET.get('show_inactive', False)
    if not show_inactive:
        all_conversations = all_conversations.filter(is_active=True)
    
    flagged_messages = Message.objects.filter(flagged_by_admin=True).select_related('sender', 'conversation')
    
    return render(request, 'messaging/admin_monitor.html', {
        'conversations': all_conversations,
        'flagged_messages': flagged_messages
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_deactivate_conversation(request, conversation_id):
    """Admin can deactivate a conversation if it violates business conduct"""
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    conversation.is_active = False
    conversation.save()
    
    # Notify both participants
    for participant in [conversation.participant_1, conversation.participant_2]:
        create_notification(
            recipient=participant,
            notification_type=Notification.EMAIL_VERIFIED,
            title="Conversation deactivated by admin",
            message=f"Your conversation about {conversation.application.job.title} has been deactivated due to policy violations.",
            related_application=conversation.application
        )
    
    messages.success(request, "Conversation deactivated.")
    return redirect('messaging:admin_monitor')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_flag_message(request, message_id):
    """Admin can flag inappropriate messages"""
    message = get_object_or_404(Message, pk=message_id)
    message.flagged_by_admin = not message.flagged_by_admin
    message.save()
    
    status = "flagged" if message.flagged_by_admin else "unflagged"
    messages.success(request, f"Message {status}.")
    return redirect('messaging:admin_monitor')
