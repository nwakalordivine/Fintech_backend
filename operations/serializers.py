from rest_framework import serializers
from auth_system.models import Wallet

class TransferSerializer(serializers.Serializer):
    recipient_account_number = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate(self, data):
        request_user = self.context['request'].user
        amount = data['amount']
        recipient_account = data['recipient_account_number']

        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")

        sender_wallet = request_user.wallet
        if sender_wallet.balance < amount:
            raise serializers.ValidationError("Insufficient wallet balance.")

        try:
            recipient_wallet = Wallet.objects.get(monnify_account_number=recipient_account)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Recipient account number not found.")

        data['recipient_wallet'] = recipient_wallet
        return data
