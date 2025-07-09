import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import UserProfile, Address
from auth_system.models import Wallet
from utilities.monnify_helper import get_monnify_token

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_wallet_and_monnify_account(sender, instance, created, **kwargs):
    """
    Automatically creates a UserProfile, Wallet, and assigns Monnify reserved account
    when a new User is created.
    """
    if not created:
        return

    profile, _ = UserProfile.objects.get_or_create(user=instance)
    Wallet.objects.get_or_create(user=instance)
    Address.objects.get_or_create(user=instance)

    if profile.monnify_account_number:
        print(f"User {instance.email} already has a Monnify account: {profile.monnify_account_number}")
        return

    try:
        token = get_monnify_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        data = {
            "accountReference": f"user_{instance.id}",
            "accountName": f"{instance.firstname} {instance.lastname}",
            "currencyCode": "NGN",
            "contractCode": settings.MONNIFY_CONTRACT_CODE,
            "customerEmail": instance.email,
            "customerName": f"{instance.firstname} {instance.lastname}"
        }

        res = requests.post(
            "https://sandbox.monnify.com/api/v1/bank-transfer/reserved-accounts",
            json=data,
            headers=headers
        )

        if res.status_code == 200:
            response = res.json()["responseBody"]
            profile.monnify_account_number = response["accountNumber"]
            profile.monnify_bank_name = response["bankName"]
            profile.bank_user_name = response["customerName"]
            profile.save()
        else:
            print("Failed to get reserved account:", res.json())

    except Exception as e:
        print(f"Error during Monnify setup: {e}")
