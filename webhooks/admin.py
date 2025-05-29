from django.contrib import admin
from .models import Organization, Payment, BalanceLog

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('inn', 'balance', 'created_at')
    search_fields = ('inn',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('operation_id', 'amount', 'payer_inn', 'document_number', 'document_date')
    search_fields = ('operation_id', 'payer_inn', 'document_number')
    list_filter = ('document_date',)
    date_hierarchy = 'document_date'
    ordering = ('-document_date',)

@admin.register(BalanceLog)
class BalanceLogAdmin(admin.ModelAdmin):
    list_display = ('organization', 'amount', 'new_balance', 'created_at')
    search_fields = ('organization__inn',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    raw_id_fields = ('organization', 'payment')