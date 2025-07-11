from django.contrib import admin

# Register your models here.
from .models import Address

class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'state', 'local_gov', 'area', 'landmark')
    search_fields = ('user__email', 'state', 'local_gov', 'area')
    list_filter = ('state', 'local_gov')
    ordering = ('user__email',)

admin.site.register(Address, AddressAdmin)
