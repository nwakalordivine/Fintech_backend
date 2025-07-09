from django.contrib import admin
from .models import User, Wallet

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'firstname', 'lastname', 'phone_number', 'is_verified', 'is_staff')
    search_fields = ('email', 'firstname', 'lastname')
    list_filter = ('is_staff',)
    ordering = ('email',)
    

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'balance')
    search_fields = ('user__email', 'user__firstname', 'user__lastname')
    list_filter = ('user__firstname',)
    ordering = ('user__email',)

    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    user_email.short_description = 'User Email'
    
admin.site.register(User, CustomUserAdmin)
admin.site.register(Wallet, WalletAdmin)