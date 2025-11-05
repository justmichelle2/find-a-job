from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<int:user_id>/<str:status>/', views.verify_user, name='verify_user'),
    path('start-verification/', views.start_email_verification, name='start_verification'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
]
