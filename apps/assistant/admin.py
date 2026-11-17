from django.contrib import admin

from .models import AssistantConfiguration, KnowledgeDocument


@admin.register(AssistantConfiguration)
class AssistantConfigurationAdmin(admin.ModelAdmin):
    fields = ('model_name', 'welcome_message', 'requests_per_minute')

    def has_add_permission(self, request):
        return not AssistantConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'slug', 'content')
    readonly_fields = ('updated_at',)
    list_per_page = 30
