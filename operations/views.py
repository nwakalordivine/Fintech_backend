from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Transaction
from rest_framework.views import APIView
from django.db import transaction as db_transaction
from .serializers import TransferSerializer
import uuid
import logging

logger = logging.getLogger(__name__)

# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny])
def monnify_webhook(request):
    data = request.data
    reference = data.get("transactionReference")
    try:
        txn = Transaction.objects.get(transaction_reference=reference)
    except Transaction.DoesNotExist:
        logger.error(f'Transaction not found for reference: {reference}')
        return Response(status=404)
    event_type = data.get("eventType")
    if event_type == "SUCCESSFUL_TRANSACTION":
        if txn.status != "success":
            with db_transaction.atomic():
                txn.status = "success"
                txn.save()
                txn.recipient.wallet.balance += txn.amount
                txn.recipient.wallet.save()
    elif event_type == "FAILED_TRANSACTION":
        with db_transaction.atomic():
            txn.status = "failed"
            txn.save()
            txn.sender.wallet.balance += txn.amount
            txn.sender.wallet.save()
    else:
        logger.info(f'Unhandled event type: {event_type}')
    return Response(status=200)


class SendMoneyView(APIView):
    def post(self, request):
        serializer = TransferSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        sender = request.user
        recipient_wallet = serializer.validated_data['recipient_wallet']
        recipient = recipient_wallet.user
        amount = serializer.validated_data['amount']
        reference = f"{sender.id}_{uuid.uuid4().hex[:10]}"
        with db_transaction.atomic():
            if sender.wallet.balance < amount:
                return Response({"error": "Insufficient funds."}, status=400)
            sender.wallet.balance -= amount
            sender.wallet.save()
            Transaction.objects.create(
                sender=sender,
                recipient=recipient,
                amount=amount,
                status='pending',
                transaction_reference=reference
            )
        logger.info(f'Transaction initiated: {reference}')
        return Response({"message": "Transaction initiated", "reference": reference}, status=201)

