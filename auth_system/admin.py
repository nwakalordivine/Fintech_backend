from django.contrib import admin
from .models import User

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'firstname', 'lastname', 'phone_number', 'is_verified', 'is_staff')
    search_fields = ('email', 'firstname', 'lastname')
    list_filter = ('is_staff',)
    ordering = ('email',)
    
admin.site.register(User, CustomUserAdmin)