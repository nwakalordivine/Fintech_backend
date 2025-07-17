from django.urls import path
from .views import (
    SendMoneyView, RequestTierUpgradeView, 
    ApproveTierUpgradeView, ListUpgradeRequestsView, 
    MonnifyWebhookView, GenerateMonnifyPaymentLink, 
    ApproveTransferOTPView, MonnifyOutTransferWebhook,
    UserTransactionsView
    )

urlpatterns = [
    path('transfer/', SendMoneyView.as_view(), name='send-money'),
    path('kyc/upgrade/tier/', RequestTierUpgradeView.as_view(), name='request-tier-upgrade'),
    path('admin/upgrade/<int:pk>/review/', ApproveTierUpgradeView.as_view(), name='review-tier-upgrade'),
    path('admin/upgrade/requests/', ListUpgradeRequestsView.as_view(), name='list-upgrade-requests'),
    path('fund/webhook/', MonnifyWebhookView.as_view(), name='monnify-webhook'),
    path('fund/wallet/', GenerateMonnifyPaymentLink.as_view(), name='fund-wallet'),
    path('transfer/webhook/', MonnifyOutTransferWebhook.as_view(), name='monnify-out-transfer-webhook'),
    path('otp/verify/<str:reference>/', ApproveTransferOTPView.as_view(), name="otp-verification-for-external-transfer"),
    path('transactions/', UserTransactionsView.as_view(), name='user-transactions'),
]