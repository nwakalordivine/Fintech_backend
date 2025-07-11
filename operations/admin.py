from django.contrib import admin

# Register your models here.
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'amount', 'status', 'transaction_reference', 'created_at')
    search_fields = ('sender__email', 'recipient__email', 'transaction_reference')
    list_filter = ('status', 'created_at')
    ordering = ('sender__id',)