from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'details')
    list_filter = ('user', 'timestamp')
    search_fields = ('action', 'details')
    date_hierarchy = 'timestamp'
    list_select_related = ('user',)
    ordering = ('-timestamp',)
    list_per_page = 50
    readonly_fields = ('timestamp', 'user', 'action', 'details')