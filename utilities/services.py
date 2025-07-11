import random
from auth_system.models import SendEmail, User as CustomUser
from rest_framework.response import Response
from django.core.mail import send_mail
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from auth_system.redis_client import redis
from utilities.monnify_helper import get_monnify_token
import requests

def generate_verification_code():
    return str(random.randint(1000, 9999))

def generate_code():
    return str(random.randint(10000, 99999))

def send_email(email, code):
    SendEmail.objects.update_or_create(email=email, defaults={'code': code})
    send_mail(
        subject='Verification Code',
        message=f'Your verification code is: \n{code}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False
    )

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

def confirm_code(email, code):
    if not email or not code:
        return "required"
    try:
        record = SendEmail.objects.get(email=email)
    except SendEmail.DoesNotExist:
        return "error"
    if record.is_expired():
        return "expired"
    if str(record.code) != str(code):
        return "invalid"
    record.is_verified = True
    record.save()
    try:
        user = CustomUser.objects.get(email=email)
        user.is_verified = True
        user.save()
        record.delete()
        return "success"
    except CustomUser.DoesNotExist:
        return "error"



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
        f"{settings.MONNIFY_BASE_URL}/bank-transfer/reserved-accounts",
        json=data,
        headers=headers
    )
    if res.status_code == 200:
          return res.json()['responseBody']
    print("Monnify Error Response:", res.text)
    raise Exception("Monnify account creation failed")

# def transaction(recipient, sender, amount, transaction_reference):
#     try:
#         recipient_user = Wallet.objects.get(monnify_account_number=recipient)
#         sender_user = Wallet.objects.get(id=sender)
#         amount = 
