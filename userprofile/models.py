from django.db import models
from django.conf import settings
# Create your models here.

class Address(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='address')
    state = models.CharField(max_length=100, null=True, blank=True, verbose_name="State")
    local_gov = models.CharField(max_length=100, null=True, blank=True, verbose_name="LGA")
    area = models.CharField(max_length=100, null=True, blank=True, verbose_name="Area")
    landmark = models.CharField(max_length=100, null=True, blank=True, verbose_name="Landmark")
    user_address = models.CharField(max_length=1000, null=True, blank=True, verbose_name="Address")

