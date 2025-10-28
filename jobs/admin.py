from django.contrib import admin
from .models import JobPost, Application


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    """
    Custom admin interface for JobPost model.
    """
    list_display = ('title', 'company', 'category', 'job_type', 'location', 'deadline', 'date_posted')
    list_filter = ('category', 'job_type', 'date_posted', 'deadline')
    search_fields = ('title', 'description', 'location', 'company__username')
    readonly_fields = ('date_posted',)
    date_hierarchy = 'date_posted'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'description', 'requirements')
        }),
        ('Job Details', {
            'fields': ('category', 'job_type', 'location', 'salary')
        }),
        ('Timeline', {
            'fields': ('date_posted', 'deadline')
        }),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Application model.
    """
    list_display = ('applicant', 'job', 'status', 'date_applied')
    list_filter = ('status', 'date_applied')
    search_fields = ('applicant__username', 'job__title', 'cover_letter')
    readonly_fields = ('date_applied',)
    date_hierarchy = 'date_applied'
    
    fieldsets = (
        ('Application Information', {
            'fields': ('applicant', 'job', 'cover_letter')
        }),
        ('Status', {
            'fields': ('status', 'date_applied')
        }),
    )
    
    actions = ['mark_as_accepted', 'mark_as_rejected']
    
    def mark_as_accepted(self, request, queryset):
        queryset.update(status='A')
    mark_as_accepted.short_description = "Mark selected applications as accepted"
    
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='R')
    mark_as_rejected.short_description = "Mark selected applications as rejected"
