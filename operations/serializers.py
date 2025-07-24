from rest_framework import serializers
from auth_system.models import Wallet
from .models import TierUpgradeRequest, Transaction
from utilities.cloudinary_helper import upload_to_cloudinary
from django.contrib.auth import get_user_model
from decimal import Decimal
User = get_user_model()

# Serializer for Transfer Operation
class TransferSerializer(serializers.Serializer):
    recipient_account_number = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transfer_type = serializers.ChoiceField(choices=['internal', 'external'], default='internal')
    description = serializers.CharField(required=False, allow_blank=True)
    bank_name = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request_user = self.context['request'].user
        amount = data['amount']
        recipient_account = data['recipient_account_number']
        transfer_type = data['transfer_type']

        if amount <= 10:
            raise serializers.ValidationError("Amount must be greater than ten.")

        sender_wallet = request_user.wallet
        if Decimal(sender_wallet.balance) < Decimal(amount):
            print(f"Sender wallet balance: {sender_wallet.balance}, Amount: {amount}")
            raise serializers.ValidationError("Insufficient wallet balance.")

        if transfer_type == 'internal':
            try:
                recipient_wallet = Wallet.objects.get(monnify_account_number=recipient_account)
                print(recipient_wallet.monnify_account_number)
            except Wallet.DoesNotExist:
                raise serializers.ValidationError("Recipient account number not found.")

            if recipient_wallet.user == request_user:
                raise serializers.ValidationError("Cannot send money to yourself.")

            data['recipient_wallet'] = recipient_wallet
            data['recipient_user'] = recipient_wallet.user
            data['destination_account_number'] = recipient_account

        else:  # external
            if not data.get('bank_name'):
                raise serializers.ValidationError("Bank name is required for external transfers.")
            data['recipient_wallet'] = None
            data['recipient_user'] = None
            data['destination_account_number'] = recipient_account

        return data
    
# Serializer for Tier Upgrade Requests
class TierUpgradeSerializer(serializers.ModelSerializer):
    id_document_file = serializers.FileField(write_only=True, required=False)
    utility_bill_file = serializers.FileField(write_only=True, required=False)
    class Meta:
        model = TierUpgradeRequest
        fields = [
            'id', 'user', 'current_tier', 'requested_tier', 'status',
            'bvn', 'id_type', 'id_document', 'utility_bill',
            'id_document_file', 'utility_bill_file', 'submitted_at'
        ]
        read_only_fields = [
            'id', 'status', 'current_tier', 'user',
            'requested_tier', 'submitted_at',
            'id_document', 'utility_bill'
        ]

    def validate(self, attrs):
        user = self.context['request'].user
        wallet = user.wallet
        current_tier = wallet.tier.lower()

        # Determine what tier they're trying to upgrade to
        next_tier = None
        if current_tier == 'tier 1':
            next_tier = 'tier 2'
        elif current_tier == 'tier 2':
            next_tier = 'tier 3'
        else:
            raise serializers.ValidationError("You are already at the highest tier.")

        attrs['current_tier'] = current_tier
        attrs['requested_tier'] = next_tier
        
        if next_tier == 'tier 2':
            bvn = attrs.get('bvn')
            if not bvn:
                raise serializers.ValidationError({"bvn": "BVN is required to upgrade to Tier 2."})
            if len(bvn) != 10:
                raise serializers.ValidationError({"bvn": "Invalid BVN format. It should be 10 digits."})
            if TierUpgradeRequest.objects.filter(bvn=bvn).exclude(id=self.context['request'].user.id).exists():
                raise serializers.ValidationError({"bvn": "This BVN is already linked to another user."})
            if User.objects.filter(bvn=bvn).exclude(id=self.context['request'].user.id).exists():
                raise serializers.ValidationError({"bvn": "This BVN is already linked to another user."})
        elif next_tier == 'tier 3':
            if not self.initial_data.get('id_type'):
                raise serializers.ValidationError({"id_type": "ID type is required for Tier 3."})
            if not self.initial_data.get('id_document_file'):
                raise serializers.ValidationError({"id_document_file": "ID document file is required."})
            if not self.initial_data.get('utility_bill_file'):
                raise serializers.ValidationError({"utility_bill_file": "Utility bill file is required."})
        return attrs

    def validate_id_document(self, value):
        if value.content_type not in [
            'application/pdf',
            'image/jpeg',
            'image/png', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]:
            raise serializers.ValidationError("Invalid file type. Only PDF, JPEG, PNG, or DOCX allowed.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        id_document_file = validated_data.pop('id_document_file', None)
        utility_bill_file = validated_data.pop('utility_bill_file', None)

        if id_document_file:
            validated_data['id_document'] = upload_to_cloudinary(id_document_file, folder_name="tier3_ids")
        if utility_bill_file:
            validated_data['utility_bill'] = upload_to_cloudinary(utility_bill_file, folder_name="tier3_utility_bills")

        return TierUpgradeRequest.objects.create(user=user, **validated_data)
    

# Serializer for Funding Wallet
class FundWalletSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_amount(self, value):
        if value <= 10:
            raise serializers.ValidationError("Amount must be greater than Ten.")
        return value

# Serializer for Monnify Fund Webhook
class MonnifyFundWebhookSerializer(serializers.Serializer):
    eventType = serializers.CharField()
    eventData = serializers.DictField()

    def validate(self, data):
        event_data = data.get("eventData", {})
        required_fields = ["paymentReference", "transactionReference", "amountPaid", "paymentStatus"]
        missing = [field for field in required_fields if field not in event_data]
        if missing:
            raise serializers.ValidationError(f"Missing fields in eventData: {missing}")
        return data
   
# Serializer for OTP Authorization
class OtpAuthorizeSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_otp(self, value):
        if not value.isdigit() and len(value) != 6:
            raise serializers.ValidationError("OTP must be a 6-digit number.")
        return value

# Serializer for Monnify Send Webhook
class MonnifySendWebhookSerializer(serializers.Serializer):
    eventType = serializers.CharField()
    eventData = serializers.DictField()

# Serializer for Tier Approval Action
class TierApprovalActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["action"] == "reject" and not data.get("reason"):
            raise serializers.ValidationError({"reason": "Reason is required when rejecting."})
        return data

# Serializer for Transaction
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
