from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'device_type', 'is_active', 'last_toggled_by', 'last_toggled_at')
    list_editable = ('is_active',)
    list_display_links = ('name',)
    list_filter = ('device_type', 'is_active')
    search_fields = ('name', 'device_type', 'last_toggled_by__username')
    list_select_related = ('last_toggled_by',)
    ordering = ('device_type',)
    list_per_page = 25
    readonly_fields = ('last_toggled_at',)