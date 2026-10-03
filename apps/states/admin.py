"""Civic AI — States Admin"""
from django.contrib import admin
from .models import State, Language, District


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'native_name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    ordering = ['display_order']


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'slug', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    filter_horizontal = ['languages']
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'native_name', 'code', 'slug', 'is_active', 'display_order', 'capital', 'region')}),
        ('Languages', {'fields': ('languages',)}),
        ('State Transition Content', {
            'fields': (
                'transition_title', 'transition_subtitle',
                'transition_image_url', 'transition_secondary_image_url',
                'transition_color_primary', 'transition_color_accent',
                'transition_landmark',
            )
        }),
    )


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'code', 'is_active']
    list_filter = ['state', 'is_active']
    search_fields = ['name']
