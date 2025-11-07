from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('request/<int:application_id>/', views.request_chat, name='request_chat'),
    path('requests/', views.chat_requests, name='chat_requests'),
    path('requests/<int:request_id>/<str:action>/', views.respond_to_chat_request, name='respond_chat_request'),
    path('conversations/', views.conversations, name='conversations'),
    path('conversation/<int:application_id>/', views.conversation_detail, name='conversation_detail'),
    path('admin/monitor/', views.admin_monitor_conversations, name='admin_monitor'),
    path('admin/deactivate/<int:conversation_id>/', views.admin_deactivate_conversation, name='admin_deactivate'),
    path('admin/flag/<int:message_id>/', views.admin_flag_message, name='admin_flag_message'),
]
