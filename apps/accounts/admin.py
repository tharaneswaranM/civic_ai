"""
Civic AI — Accounts Admin
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, OTPRequest


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['mobile_number', 'full_name', 'preferred_language', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'preferred_language', 'preferred_state']
    search_fields = ['mobile_number', 'full_name', 'email']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('mobile_number', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'email')}),
        (_('Preferences'), {'fields': ('preferred_language', 'preferred_state')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Privacy'), {'fields': ('consent_data_processing', 'consent_date')}),
        (_('Important dates'), {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('mobile_number',),
        }),
    )
    readonly_fields = ['date_joined', 'last_login']


@admin.register(OTPRequest)
class OTPRequestAdmin(admin.ModelAdmin):
    list_display = ['mobile_number', 'purpose', 'status', 'attempts', 'created_at', 'expires_at']
    list_filter = ['status', 'purpose']
    search_fields = ['mobile_number']
    readonly_fields = ['otp_hash']  # Never display OTP
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False  # OTPs are system-generated only
