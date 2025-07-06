import random
from .models import SendEmail, User as CustomUser
from rest_framework.response import Response
from django.core.mail import send_mail
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from .redis_client import redis

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
    try:
        if not email or not code:
            return "required"
        record = SendEmail.objects.get(email=email)
        if record.is_expired():
            return "expired"
        if str(record.code) != str(code):
            return "invalid"
        record.is_verified = True
        record.save()
        return "success"
    except SendEmail.DoesNotExist:
        return "error"

def password_reset(email):
    user = get_object_or_404(CustomUser, email=email)
    code = generate_code()
    redis.set(f"reset:{user.id}", code, ex=600)  # 10 minutes TTL
    reset_url = f"{settings.FRONTEND_URL}/reset-password?id={user.id}&code={code}"
    try:
        send_mail(
            "Password Reset",
            f"Hello\nClick the link to reset your password:\n {reset_url}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
    except Exception as e:
        raise Exception(f"Email sending failed: {str(e)}")
    return "success"

def password_reset_confirm(id, code, new_password):
    try:
        id = int(id)
    except ValueError:
        return "invalid_id"
    stored_code = redis.get(f"reset:{id}")
    if stored_code is None:
        return "expired"
    if stored_code != code:
        return "invalid"
    try:
        user = CustomUser.objects.get(id=id)
        user.set_password(new_password)
        user.save()
        redis.delete(f"reset:{id}")
        return "success"
    except CustomUser.DoesNotExist:
        return "not_found"
