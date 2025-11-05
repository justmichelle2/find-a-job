from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('choose-account-type/', views.choose_account_type, name='choose_account_type'),
    path('choose-verification-method/', views.choose_verification_method, name='choose_verification_method'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<int:user_id>/<str:status>/', views.verify_user, name='verify_user'),
    path('start-verification/', views.start_email_verification, name='start_verification'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('resend-code/', views.resend_verification_code, name='resend_code'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('start-phone-verification/', views.start_phone_verification, name='start_phone_verification'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
]
