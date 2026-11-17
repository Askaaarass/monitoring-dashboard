from django.contrib import admin

from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'amount',
        'currency',
        'payment_provider',
        'payment_status',
        'is_anonymous',
        'created_at',
        'paid_at',
    )
    list_filter = ('payment_status', 'payment_provider', 'is_anonymous', 'created_at')
    search_fields = ('id', 'provider_payment_id', 'donor_name', 'donor_email')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'id',
        'idempotency_key',
        'payment_provider',
        'provider_payment_id',
        'payment_url',
        'amount',
        'currency',
        'donor_name',
        'donor_email',
        'is_anonymous',
        'payment_status',
        'created_at',
        'paid_at',
    )
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
