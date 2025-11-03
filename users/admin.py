from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin interface for CustomUser model with is_company field.
    """
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_company', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_company', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    date_hierarchy = 'date_joined'

    fieldsets = UserAdmin.fieldsets + (('Account Type', {
        'fields': ('is_company', )
    }), )

    add_fieldsets = UserAdmin.add_fieldsets + (('Account Type', {
        'fields': ('is_company', )
    }), )
