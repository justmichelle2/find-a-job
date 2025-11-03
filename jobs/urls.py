from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.JobListView.as_view(), name='job_list'),
    path('job/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('apply/<int:pk>/', views.apply_job, name='apply_job'),
    path('create/', views.create_job_post, name='create_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    
    path('dashboards/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboards/company/', views.company_dashboard, name='company_dashboard'),
    path('dashboards/student/', views.student_dashboard, name='student_dashboard'),
    
    path('application/<int:pk>/status/<str:status>/', views.update_application_status, name='update_application_status'),
    path('job/<int:pk>/edit/', views.edit_job, name='edit_job'),
    path('job/<int:pk>/delete/', views.delete_job, name='delete_job'),
    path('job/<int:pk>/approve/', views.approve_job, name='approve_job'),
]

