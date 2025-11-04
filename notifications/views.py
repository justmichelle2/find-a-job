from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Notification

@login_required
def notification_list(request):
    """View to display user's notifications"""
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.update(is_read=True)
        return redirect('notifications:list')
        
    # Paginate notifications
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page = request.GET.get('page')
    notifications = paginator.get_page(page)
    
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_as_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = Notification.objects.get(id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications:list')