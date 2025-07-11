from rest_framework import serializers
from .models import SendEmail
from django.contrib.auth import get_user_model
from utilities.cloudinary_helper import upload_image_to_cloudinary

CustomUser = get_user_model()

class SendEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SendEmail
        fields = ['id', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email field cannot be empty.")
        return value
    
class CodeVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    
    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("Code field cannot be empty.")
        if not value.isdigit() or len(value) != 4:
            raise serializers.ValidationError("Code must be a 4-digit number.")
        return value


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(write_only=True, required=False)
    class Meta:
        model = CustomUser
        fields = ['id', 'firstname', 'lastname', 'email', 'password', 'phone_number', 'image', 'is_admin', 'is_verified', 'date_of_birth']
        read_only_fields = ['id', 'is_staff', 'is_admin']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email field cannot be empty.")
        return value

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("Password field cannot be empty.")
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def validate_phone_number(self, value):
        if value and len(value) != 11:
            raise serializers.ValidationError("Phone number must be 11 digits.")
        user_qs = CustomUser.objects.filter(phone_number=value)
        if self.instance:
            user_qs = user_qs.exclude(pk=self.instance.pk)
        if user_qs.exists():
            raise serializers.ValidationError("User with this phone number already exists.")
        return value
    
    def create(self, validated_data):
        image_file = validated_data.get('image', None)
        if image_file:
            image_url = upload_image_to_cloudinary(image_file, folder_name="fintechapp_user_images")
            validated_data['image'] = image_url
        customuser = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            firstname=validated_data.get('firstname').title(),
            lastname=validated_data.get('lastname').title(),
            phone_number=validated_data.get('phone_number'),
            image=validated_data.get('image'),
        )

        from .models import Wallet
        if not hasattr(customuser, 'wallet'):
            Wallet.objects.create(user=customuser)
        return customuser

    def get_wallet_balance(self, obj):
        wallet = getattr(obj, 'wallet', None)
        if wallet:
            return "{:.2f}".format(wallet.balance)
        return "0.00"
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        wallet = getattr(instance, 'wallet', None)
        if wallet:
            rep["image"] = instance.image
            rep["account_details"] = {
                "monnify_account_number": wallet.monnify_account_number if wallet else None,
                "monnify_bank_name": wallet.monnify_bank_name if wallet else None,
                "bank_user_name": wallet.bank_user_name if wallet else None,
                "account_reference": wallet.accountreference if wallet else None,
                "tier": wallet.tier if wallet else None,
                "wallet_balance": "{:.2f}".format(wallet.balance) if wallet else "0.00"
            }
            return rep

    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True)
    code = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new_password = attrs['new_password']
        confirm_password = attrs['confirm_password']
        code = attrs['code']
        if not new_password or not confirm_password:
            raise serializers.ValidationError("Both password fields are required.")

        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password do not match.")

        if len(new_password) < 8:
            raise serializers.ValidationError("New password must be at least 8 characters long.")
        if not code.isdigit() or len(code) != 5:
            raise serializers.ValidationError("Code must be a 5-digit number.")
        return attrs

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
