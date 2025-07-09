from django.contrib import admin

# Register your models here.
from .models import UserProfile, Address

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'monnify_account_number', 'monnify_bank_name', 'bank_user_name','date_of_birth')
    search_fields = ('user__email', 'monnify_account_number', 'monnify_bank_name')
    list_filter = ('tier',)
    ordering = ('user__email',)

class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'state', 'local_gov', 'area', 'landmark')
    search_fields = ('user__email', 'state', 'local_gov', 'area')
    list_filter = ('state', 'local_gov')
    ordering = ('user__email',)

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Address, AddressAdmin)
