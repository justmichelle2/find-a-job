from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<int:user_id>/<str:status>/', views.verify_user, name='verify_user'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verify-code/', views.verify_code, name='verify_code'),
]
