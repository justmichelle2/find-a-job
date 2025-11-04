from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'verification_date')
    search_fields = ('user__username', 'user__email')
    list_filter = ('is_verified',)

admin.site.register(UserProfile, UserProfileAdmin)