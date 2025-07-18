from django.db import models
from auth_system.models import User
from django.conf import settings
from django.utils import timezone

# Create your models here.
TIER_CHOICES = [
    ('tier 1', 'Tier 1'),
    ('tier 2', 'Tier 2'),
    ('tier 3', 'Tier 3'),
]

ID_TYPE_CHOICES = [
    ('nin', 'NIN Slip'),
    ('voter_card', "Voter's Card"),
    ('driver_license', "Driver's License"),
    ('passport', 'International Passport'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    TRANSACTION_TYPES = [
        ('Deposit', 'Deposit'),
        ('Debit', 'Debit'),
        ('Credit', 'Credit'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    source_account_number = models.CharField(max_length=15, blank=True, null=True)
    destination_account_number = models.CharField(max_length=15, blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='Debit')
    transfer_type = models.CharField(max_length=20, choices=[('internal', 'Internal'), ('external', 'External')], default='internal')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    transaction_reference = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)



class TierUpgradeRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    requested_tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    bvn = models.CharField(max_length=11, null=True, blank=True)
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, null=True, blank=True)
    id_document = models.URLField(max_length=1000, null=True, blank=True)
    utility_bill = models.URLField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.current_tier} ➜ {self.requested_tier} ({self.status})"


class DailyLimitTracker(models.Model):
    user = models.OneToOneField('auth_system.User', on_delete=models.CASCADE, related_name='daily_limit')
    date = models.DateField(default=timezone.now)
    daily_inflow = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    daily_outflow = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def reset_if_new_day(self):
        if self.date != timezone.now().date():
            self.daily_inflow = 0
            self.daily_outflow = 0
            self.date = timezone.now().date()
            self.save()
