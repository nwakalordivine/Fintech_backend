import random
from auth_system.models import User as CustomUser
from rest_framework.response import Response
from django.core.mail import send_mail
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from auth_system.redis_client import redis
from utilities.monnify_helper import get_monnify_token
import requests
from operations.models import DailyLimitTracker

# Utility functions for user operations

def generate_verification_code():
    return str(random.randint(1000, 9999))

def generate_code():
    return str(random.randint(10000, 99999))

def check_users(email):
    try:
        CustomUser.objects.get(email=email)
        return Response(
            {"message": "User exists in database", "email": email},
            status=status.HTTP_200_OK
        )
    except CustomUser.DoesNotExist:
        return Response(
            {"message": "User does not exist in database", "email": email},
            status=status.HTTP_404_NOT_FOUND
        )

def password_reset(email):
    user = get_object_or_404(CustomUser, email=email)
    code = generate_code()
    redis.set(f"reset:{user.email}", code, ex=600)  # 10 minutes TTL
    reset = f"your reset code is: \n{code}"
    try:
        send_mail(
            "Password Reset",
            f"Hello\n{reset}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
    except Exception as e:
        raise Exception(f"email sending failed: {str(e)}")
    return "success"

def password_reset_confirm(email, code, new_password):
    stored_code = redis.get(f"reset:{email}")
    if stored_code is None:
        return "expired"
    if stored_code != code:
        return "invalid"
    try:
        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        redis.delete(f"reset:{email}")
        return "success"
    except CustomUser.DoesNotExist:
        return "not_found"

def create_reserved_account(user):
    token = get_monnify_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "accountReference": f"user_{user.id}",
        "accountName": f"{user.firstname.title()} {user.lastname.title()}",
        "currencyCode": "NGN",
        "contractCode": settings.MONNIFY_CONTRACT_CODE,
        "customerEmail": user.email,
        "customerName": f"{user.firstname} {user.lastname}"
    }
    res = requests.post(
        f"{settings.MONNIFY_BASE_URL}api/v1/bank-transfer/reserved-accounts",
        json=data,
        headers=headers
    )
    if res.status_code == 200:
          return res.json()['responseBody']
    print("Monnify Error Response:", res.text)
    raise Exception("Monnify account creation failed")

def enforce_tier_rules(sender, amount):
    tracker, _ = DailyLimitTracker.objects.get_or_create(user=sender)
    tracker.reset_if_new_day()
    tier = sender.wallet.tier.lower()
    rules = settings.TIER_RULES.get(tier)
    if not rules or tracker.daily_outflow + amount > rules["daily_outflow"]:
        return False
    tracker.daily_outflow += amount
    tracker.save()
    return True

def handle_monnify_response(response, reference):
    if response.status_code == 200 and response.json().get("requestSuccessful") and response.json().get("responseBody")["status"] == "PENDING_AUTHORIZATION":
        return Response({
        "message": "OTP required. Please check your registered email.",
        "transaction_reference": reference,
        "status": "pending_authorization"
        }, status=response.status_code)
    

