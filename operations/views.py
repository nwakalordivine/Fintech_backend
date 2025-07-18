from rest_framework.response import Response
from .models import Transaction, DailyLimitTracker, TierUpgradeRequest
from rest_framework.views import APIView, status
from django.db import transaction as db_transaction
from .serializers import (
    TransferSerializer, TierUpgradeSerializer,
    TierApprovalActionSerializer, FundWalletSerializer, 
    MonnifyFundWebhookSerializer, MonnifySendWebhookSerializer, OtpAuthorizeSerializer, TransactionSerializer)
import uuid
from rest_framework import serializers, generics
from django.utils import timezone
from django.conf import settings
from rest_framework.permissions import BasePermission, IsAuthenticated
import requests
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from utilities.monnify_helper import get_monnify_token, get_bank_code, initiate_transfer
from utilities.services import handle_monnify_response
from auth_system.models import Wallet

# Create your views here.

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_admin

@method_decorator(csrf_exempt, name='dispatch')
class MonnifyOutTransferWebhook(APIView):
    serializer_class = MonnifySendWebhookSerializer
    authentication_classes = []
    permission_classes = []      

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data["eventData"]
        event_type = serializer.validated_data["eventType"]

        transaction_ref = data.get('reference')

        try:
            deposit = Transaction.objects.get(transaction_reference=transaction_ref)

            if deposit.status != "pending":
                return Response({"message": "Already processed."}, status=200)

            if event_type != "SUCCESSFUL_DISBURSEMENT":
                sender = deposit.sender

                sender_wallet = Wallet.objects.get(sender=sender)
                sender_wallet.balance += deposit.amount
                sender_wallet.save()
                return Response({"message": "Not a successful transaction event"}, status=200)
            tracker, _ = DailyLimitTracker.objects.get_or_create(user=deposit.user)
            tracker.reset_if_new_day()
            tracker.daily_outflow += Decimal(data["amount"])
            tracker.save()
            if data.get('status') == "SUCCESS":
                with db_transaction.atomic():
                    deposit.status = "success"
                    deposit.fee = float(data["fee"])
                    deposit.save()
            else:
                deposit.status = "failed"
                deposit.save()

            return Response({"message": "Processed"}, status=200)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found."}, status=404)

class ApproveTransferOTPView(APIView):
    serializer_class = OtpAuthorizeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, reference):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data["otp"]

        url = f"{settings.MONNIFY_BASE_URL}api/v2/disbursements/single/validate-otp"
        access_token = get_monnify_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }  
        payload = {
            "reference": reference,
            "authorizationCode": otp
            }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if data.get("requestSuccessful"):
            return Response({"message": "OTP approved. Await webhook for transaction update."}, status=200)
        return Response({
            "error": "OTP verification failed.",
            "monnify_response": data
        }, status=400)

class SendMoneyView(APIView):
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        sender = request.user
        sender_wallet = sender.wallet

        amount = serializer.validated_data['amount']
        transfer_type = serializer.validated_data['transfer_type']
        bank_name = serializer.validated_data.get('bank_name')
        description = serializer.validated_data.get('description', '')
        recipient_wallet = serializer.validated_data.get('recipient_wallet')
        recipient = serializer.validated_data.get('recipient_user')
        destination_account_number = serializer.validated_data['destination_account_number']

        tracker, _ = DailyLimitTracker.objects.get_or_create(user=sender)
        tracker.reset_if_new_day()

        tier = sender_wallet.tier.lower()
        rules = settings.TIER_RULES.get(tier)
        if not rules:
            return Response({"error": f"No rules defined for tier '{tier}'"}, status=400)

        if tracker.daily_outflow + amount > rules["daily_outflow"]:
            return Response({"error": "Daily outflow limit exceeded."}, status=400)

        if sender_wallet.balance < amount:
            return Response({"error": "Insufficient funds."}, status=400)

        reference = f"{sender.id}_{uuid.uuid4().hex[:10]}"

        if transfer_type == "internal":
            recipient_tier = recipient_wallet.tier.lower()
            recipient_rules = settings.TIER_RULES.get(recipient_tier)
            if recipient_wallet.balance + amount > recipient_rules["max_balance"]:
                return Response({"error": "Recipient's wallet balance limit exceeded."}, status=400)
            r_tracker, _ = DailyLimitTracker.objects.get_or_create(user=recipient)
            r_tracker.reset_if_new_day()
            if r_tracker.daily_inflow + amount > recipient_rules["daily_inflow"]:
                return Response({"error": "recipient's daily Inflow limit exceeded."}, status=400)
            r_tracker.daily_inflow += amount
            r_tracker.save()
            
            with db_transaction.atomic():
                sender_wallet.balance -= amount
                recipient_wallet.balance += amount
                sender_wallet.save()
                recipient_wallet.save()

                tracker.daily_outflow += amount
                tracker.save()

                Transaction.objects.create(
                    user=sender,
                    sender_name=f"{sender.firstname} {sender.lastname}",
                    recipient_name=f"{recipient.firstname} {recipient.lastname}",
                    transfer_type='internal',
                    amount=amount,
                    status='success',
                    bank_name="Monniepoint",
                    description=description,
                    transaction_reference=reference + "_debit",
                    transaction_type="Debit"
                )
                Transaction.objects.create(
                    user=recipient,
                    sender_name=f"{sender.firstname} {sender.lastname}",
                    recipient_name=f"{recipient.firstname} {recipient.lastname}",
                    transfer_type='internal',
                    amount=amount,
                    status='success',
                    bank_name="Monniepoint",
                    description=description,
                    transaction_reference=reference + "_credit",
                    transaction_type="Credit"
                )

            return Response({"message": "Transaction successful", "reference": reference}, status=201)

        else:
            if not bank_name:
                return Response({"error": "Bank name is required for external transfers."}, status=400)

            bank_code, bank_title, recipient_name= get_bank_code(bank_name, destination_account_number)
            if not bank_code:
                return Response({"error": f"Bank code for '{bank_name}' not found."}, status=400)

            with db_transaction.atomic():
                sender_wallet.balance -= amount
                sender_wallet.save()

                Transaction.objects.create(
                    user=sender,
                    sender_name=f"{sender.firstname} {sender.lastname}",
                    recipient_name=recipient_name.title() if recipient_name else bank_title,
                    transfer_type='external',
                    amount=amount,
                    status='pending',
                    source_account_number=sender_wallet.monnify_account_number,
                    destination_account_number=destination_account_number,
                    bank_name=bank_title,
                    description=description,
                    transaction_reference=reference
                )

                response = initiate_transfer(
                    amount=amount,
                    reference=reference,
                    bank_name=bank_name,
                    description=description,
                    destination=destination_account_number,
                    bank_code=bank_code
                )

                return handle_monnify_response(
                    response=response,
                    reference=reference,
                )
            return Response({"error": "External transfers not supported in this version."}, status=400)

class RequestTierUpgradeView(generics.CreateAPIView):
    serializer_class = TierUpgradeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        existing = TierUpgradeRequest.objects.filter(user=user, status="pending")
        if existing.exists():
            raise serializers.ValidationError("You already have a pending upgrade request.")
        serializer.save()

class ApproveTierUpgradeView(generics.UpdateAPIView):
    queryset = TierUpgradeRequest.objects.all()
    serializer_class = TierApprovalActionSerializer
    permission_classes = [IsAdmin]

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upgrade_request = self.get_object()

        if upgrade_request.status != 'pending':
            return Response({"error": "Request already processed."}, status=400)

        action = serializer.validated_data['action']
        upgrade_request.status = 'approved' if action == 'approve' else 'rejected'
        upgrade_request.reviewed_at = timezone.now()
        upgrade_request.save()

        if action == 'approve':
            wallet = upgrade_request.user.wallet
            wallet.tier = upgrade_request.requested_tier
            wallet.save()

            if upgrade_request.bvn and upgrade_request.requested_tier.lower() == 'tier 2':
                user = upgrade_request.user
                if not user.bvn:
                    user.bvn = upgrade_request.bvn
                    user.save()

        return Response({"message": f"Request {action}d successfully."})


class ListUpgradeRequestsView(generics.ListAPIView):
    queryset = TierUpgradeRequest.objects.all().order_by('-submitted_at')
    serializer_class = TierUpgradeSerializer
    permission_classes = [IsAdmin]

class GenerateMonnifyPaymentLink(APIView):
    serializer_class = FundWalletSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FundWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        user = request.user
        tracker, _ = DailyLimitTracker.objects.get_or_create(user=user)
        tracker.reset_if_new_day()
        tier = user.wallet.tier.lower()
        rules = settings.TIER_RULES.get(tier)
        if tracker.daily_inflow + amount > rules["daily_inflow"]:
            return Response({"error": "Daily Inflow limit exceeded."}, status=400)
        if user.wallet.balance + amount > rules["max_balance"]:
            return Response({"error": "wallet balance limit exceeded."}, status=400)
        payment_reference = str(uuid.uuid4())
        Transaction.objects.create(
            user=user,
            sender_name=f"{user.firstname} {user.lastname}",
            recipient_name="Wallet Funding",
            amount=amount,
            transfer_type="internal",
            transaction_type="Deposit",
            status="pending",
            transaction_reference=payment_reference,
            bank_name="Monniepoint",
            description="Wallet Funding via Monnify"
        )

        payload = {
            "amount": float(amount),
            "customerName": f"{request.user.firstname} {request.user.lastname}",
            "customerEmail": request.user.email,
            "paymentReference": payment_reference,
            "paymentDescription": "Wallet Funding",
            "currencyCode": "NGN",
            "contractCode": settings.MONNIFY_CONTRACT_CODE
        }
        access_token = get_monnify_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{settings.MONNIFY_BASE_URL}api/v1/merchant/transactions/init-transaction",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            response_data = response.json()['responseBody']
            return Response({
                "payment_link": response_data['checkoutUrl'],
                "payment_reference": payment_reference
            })
        return Response(response.json(), status=response.status_code)
    
@method_decorator(csrf_exempt, name='dispatch')
class MonnifyWebhookView(APIView):
    serializer_class = MonnifyFundWebhookSerializer
    authentication_classes = []
    permission_classes = []      

    def post(self, request):
        serializer = MonnifyFundWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data["eventData"]
        event_type = serializer.validated_data["eventType"]

        payment_ref = data.get('paymentReference')
        transaction_ref = data.get('transactionReference')
        amount_paid = data.get('amountPaid')
        payment_status = data.get('paymentStatus')

        try:
            deposit = Transaction.objects.get(transaction_reference=payment_ref, transaction_type='Deposit')
            deposit.transaction_reference = transaction_ref
             
            if deposit.status != "pending":
                return Response({"message": "Already processed."}, status=200)

            if event_type != "SUCCESSFUL_TRANSACTION":
                return Response({"message": "Not a successful transaction event"}, status=200)

            if payment_status == "PAID":
                with db_transaction.atomic():
                    deposit.status = "success"
                    deposit.save()

                    wallet = deposit.user.wallet
                    wallet.balance += Decimal(str(amount_paid))
                    wallet.save()


            else:
                deposit.status = "failed"
                deposit.save()

            return Response({"message": "Processed"}, status=200)

        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found."}, status=404)

class UserTransactionsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get(self, request):
        user = request.user
        sent_transactions = Transaction.objects.filter(user=user).order_by('-created_at')
        sent_data = self.serializer_class(sent_transactions, many=True).data
        return Response(
            sent_data, status=status.HTTP_200_OK
            )

