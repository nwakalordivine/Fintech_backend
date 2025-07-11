from django.urls import path
from .views import SendMoneyView, monnify_webhook


urlpatterns = [
    path('webhook/monnify/', monnify_webhook, name='monnify-webhook'),
    path('send-money/', SendMoneyView.as_view(), name='send-money'),
]