from django.db import models
from django.conf import settings
# Create your models here.

TIER_CHOICES = [
    ('tier 1', 'Tier 1'),
    ('tier 2', 'Tier 2'),
    ('tier 3', 'Tier 3'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='Tier 1')
    date_of_birth = models.DateField(null=True, blank=True)
    monnify_account_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    monnify_bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_user_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} Profile"

    def get_max_balance(self):
        return {
            'Tier 1': 50000,
            'Tier 2': 200000,
            'Tier 3': 5000000,
        }[self.tier]

    def get_daily_limit(self):
        return {
            'Tier 1': 20000,
            'Tier 2': 100000,
            'Tier 3': 1000000,
        }[self.tier]
    
class Address(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='address')
    state = models.CharField(max_length=100, null=True, blank=True, verbose_name="State")
    local_gov = models.CharField(max_length=100, null=True, blank=True, verbose_name="LGA")
    area = models.CharField(max_length=100, null=True, blank=True, verbose_name="Area")
    landmark = models.CharField(max_length=100, null=True, blank=True, verbose_name="Landmark")
    user_address = models.CharField(max_length=1000, null=True, blank=True, verbose_name="Address")

