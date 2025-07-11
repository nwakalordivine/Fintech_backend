from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from utilities.services import create_reserved_account
from auth_system.models import Wallet
from userprofile.models import Address

User = get_user_model()

@receiver(post_save, sender=User)
def create_wallet_and_monnify_account(sender, instance, created, **kwargs):
    """
    Automatically creates a Wallet and assigns Monnify reserved account
    when a new User is created.
    """
    if not created:
        return

    wallet, _ = Wallet.objects.get_or_create(user=instance)
    Address.objects.get_or_create(user=instance)

    try:
        details = create_reserved_account(instance)
        wallet.monnify_account_number = details["accountNumber"]
        wallet.monnify_bank_name = details["bankName"]
        wallet.bank_user_name = details["customerName"]
        wallet.accountreference = details["accountReference"]
        wallet.save()
    except Exception as e:
        print(f"Error during Monnify setup: {e}")
