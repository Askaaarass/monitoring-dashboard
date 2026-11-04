from django.contrib import admin
from .models import BiomassIndex, Sensor, SensorData, Alert


@admin.register(BiomassIndex)
class BiomassIndexAdmin(admin.ModelAdmin):
    list_display = ('value',)
    fields = ('value',)
    list_per_page = 20

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sensor_type', 'unit', 'min_threshold', 'max_threshold', 'is_active')
    list_editable = ('min_threshold', 'max_threshold', 'is_active')
    list_display_links = ('name',)
    list_filter = ('sensor_type', 'is_active', 'is_auto')
    search_fields = ('name', 'sensor_type', 'unit')
    ordering = ('sensor_type',)
    list_per_page = 25

@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'value', 'timestamp')
    list_filter = ('sensor', 'timestamp')
    search_fields = ('sensor__name',)
    date_hierarchy = 'timestamp'
    list_select_related = ('sensor',)
    ordering = ('-timestamp',)
    list_per_page = 50
    readonly_fields = ('timestamp',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'severity', 'message', 'is_resolved', 'created_at')
    list_filter = ('severity', 'is_resolved', 'sensor')
    list_editable = ('is_resolved',)
    list_display_links = ('message',)
    search_fields = ('sensor__name', 'message')
    date_hierarchy = 'created_at'
    list_select_related = ('sensor',)
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)