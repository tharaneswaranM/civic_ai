"""Civic AI — Schemes Admin"""
from django.contrib import admin
from .models import (
    SchemeCategory, Department, Scheme, SchemeVersion,
    EligibilityRule, RequiredDocument, SchemeTranslation,
    UserSchemeMatch, SavedScheme
)


@admin.register(SchemeCategory)
class SchemeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'state', 'is_central']
    list_filter = ['state', 'is_central']
    search_fields = ['name']


class EligibilityRuleInline(admin.TabularInline):
    model = EligibilityRule
    extra = 1
    fields = ['rule_type', 'operator', 'value', 'is_mandatory', 'display_label']


class RequiredDocumentInline(admin.TabularInline):
    model = RequiredDocument
    extra = 1
    fields = ['name', 'is_mandatory', 'description', 'display_order']


@admin.register(SchemeVersion)
class SchemeVersionAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'version_number', 'review_status', 'effective_from', 'extracted_by_ai']
    list_filter = ['review_status', 'extracted_by_ai']
    inlines = [EligibilityRuleInline, RequiredDocumentInline]
    actions = ['approve_versions', 'reject_versions']

    def approve_versions(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(review_status='approved', reviewed_by=request.user, reviewed_at=timezone.now())
        # Set as current version for each scheme
        for version in queryset:
            version.scheme.current_version = version
            version.scheme.save(update_fields=['current_version'])
        self.message_user(request, f'{updated} version(s) approved.')
    approve_versions.short_description = 'Approve selected versions'

    def reject_versions(self, request, queryset):
        from django.utils import timezone
        queryset.update(review_status='rejected', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, 'Selected versions rejected.')
    reject_versions.short_description = 'Reject selected versions'


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'status', 'state', 'is_featured', 'is_new', 'created_at']
    list_filter = ['level', 'status', 'state', 'is_featured', 'is_new']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['categories']
    list_editable = ['is_featured', 'is_new', 'status']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserSchemeMatch)
class UserSchemeMatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'scheme', 'result', 'evaluated_at']
    list_filter = ['result']
    search_fields = ['user__mobile_number', 'scheme__name']
    readonly_fields = ['evaluated_at']
