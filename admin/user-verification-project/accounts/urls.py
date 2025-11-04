from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify/<int:user_id>/', views.verify_user, name='verify_user'),
]